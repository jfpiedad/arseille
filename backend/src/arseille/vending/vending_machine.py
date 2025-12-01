import asyncio
import time
from typing import AsyncGenerator

import mediapipe
from cv2 import VideoCapture
from mediapipe.tasks.python.components.containers.detections import DetectionResult
from mediapipe.tasks.python.vision.face_detector import FaceDetector

from arseille.config import settings
from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.ml_models.face_detection.inference import initialize_face_detector
from arseille.vending.checkpoints import (
    BaseCheckpoint,
    Checkpoint25Percent,
    Checkpoint50Percent,
    Checkpoint75Percent,
)
from arseille.vending.data import DetectionMetadata
from arseille.vending.enums import VendingMode
from arseille.vending.exceptions import InvalidCameraIndex, InvalidVendingMode
from arseille.vending.utils import TaskExecutor


class VideoSource:
    def __init__(self, index: int = 0) -> None:
        """
        Initialize a video source using OpenCV's VideoCapture.

        Attributes:
            index (int): The camera index to use on initialization.
        """
        self.video_feed = VideoCapture(index=index)

        if not self.video_feed.isOpened() or self.video_feed is None:
            raise InvalidCameraIndex

    async def read(self) -> AsyncGenerator[tuple[mediapipe.Image, int], None]:
        """
        Asynchronously yields frames from the webcam.

        Each iteration returns a tuple `(image, timestamp)`, where:
            - `image` is the captured frame converted to a `mediapipe.Image` in
            in RGB format.
            - `timestamp` is the capture time in milliseconds since the epoch.
        """
        while True:
            success, frame = await asyncio.to_thread(self.video_feed.read)

            if not success:
                print("Could not read frame.")
                break

            timestamp_ms = int(round(time.time() * 1000))
            image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=frame)

            yield image, timestamp_ms

    def close(self) -> None:
        """Close the video source and release its resources."""
        self.video_feed.release()


class VendingMachine:
    """
    The vending machine class.

    It is designed to only process one user at a time just like
    how a real vending machine would.
    """

    _mode: VendingMode
    _modes_mapping: dict[VendingMode, BaseCheckpoint]

    def __init__(
        self,
        video_source: VideoSource,
        face_detector: FaceDetector,
        age_estimator: AgeEstimator,
        task_executor: TaskExecutor,
    ) -> None:
        """
        Initializes the vending machine object and its dependencies.

        Attributes:
            video_source (VideoSource): The video feed which produces frames.
            face_detector (FaceDetector): The face detector model object from MediaPipe.
            age_estimator (AgeEstimator): The age estimator model object.
            task_executor (TaskExecutor): Executor where tasks are submitted and
             offloaded to a thread.
        """
        self.video_source = video_source
        self.face_detector = face_detector
        self.age_estimator = age_estimator
        self.task_executor = task_executor

        self.metadata_obj = DetectionMetadata()

        self._checkpoint25 = Checkpoint25Percent()
        self._checkpoint50 = Checkpoint50Percent()
        self._checkpoint75 = Checkpoint75Percent()

        self._mode = None
        self._modes_mapping = {
            VendingMode.CHECKPOINT_25: self._checkpoint25,
            VendingMode.CHECKPOINT_50: self._checkpoint50,
            VendingMode.CHECKPOINT_75: self._checkpoint75,
        }

        self._lock = asyncio.Lock()

    @classmethod
    def create_standard(cls) -> "VendingMachine":
        """Creates the vending machine object with standard configuration."""
        vm = cls(
            video_source=VideoSource(),
            face_detector=None,
            age_estimator=AgeEstimator(
                weights_path=settings.AGE_ESTIMATOR_WEIGHTS_PATH
            ),
            task_executor=TaskExecutor(workers=2),
        )

        vm.face_detector = initialize_face_detector(
            model_asset_path=settings.FACE_DETECTOR_WEIGHTS_PATH_INFERENCE,
            result_callback=vm.result_callback,
        )

        return vm

    def set_mode(self, mode: VendingMode) -> None:
        self._mode = mode

    async def set_unavailable(self) -> None:
        if self._mode not in self._modes_mapping:
            raise InvalidVendingMode

        await self._lock.acquire()

    def set_available(self) -> None:
        if self._lock.locked():
            self._lock.release()

    def clear_metadata_obj(self) -> None:
        self.metadata_obj.clear()

    def clear_recent_detection_results(self) -> None:
        self._checkpoint50.recent_detection_results.clear()
        self._checkpoint75.recent_detection_results.clear()

    def cleanup(self) -> None:
        """
        Release the following resources:

        - Face detector's task runner (mediapipe vision task instance).
        - OpenCV's VideoCapture
        - ThreadPoolExecutor
        """

        self.face_detector.close()
        self.video_source.close()
        self.task_executor.shutdown()

    def result_callback(
        self,
        detection_result: DetectionResult,
        output_image: mediapipe.Image,
        timestamp_ms: int,
    ) -> None:
        """Callback function after a successful face detection."""
        self.metadata_obj.timestamp = timestamp_ms
        image = output_image.numpy_view()

        self._modes_mapping[self._mode].process(
            metadata_obj=self.metadata_obj,
            detection_result=detection_result,
            image=image,
            age_estimator=self.age_estimator,
            executor=self.task_executor,
        )
