import asyncio
import time
from typing import AsyncGenerator

import cv2
import mediapipe
from cv2 import VideoCapture
from fastapi import WebSocket
from mediapipe.tasks.python.components.containers.detections import DetectionResult
from mediapipe.tasks.python.vision.face_detector import FaceDetector
from pymongo.asynchronous.database import AsyncDatabase

from arseille.config import settings
from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.ml_models.face_detection.inference import initialize_face_detector
from arseille.vending.checkpoints import (
    BaseVMCheckpoint,
    VMCheckpoint25,
    VMCheckpoint50,
    VMCheckpoint75,
    VMFullSystem,
)
from arseille.vending.data import DetectionMetadata
from arseille.vending.enums import VendingMode
from arseille.vending.exceptions import InvalidCameraIndex, InvalidVendingMode
from arseille.vending.utils import TaskExecutor


class VideoSource:
    """
    Initialize a video source using OpenCV's VideoCapture.

    Attributes:
        video_feed (VideoCapture): OpenCV's video capture object.
    """

    def __init__(self, index: int = 0) -> None:
        """
        Initialize a video source.

        Args:
            index (int): The camera index to use on initialization.
        """
        self.video_feed = VideoCapture(index=index)

        if not self.video_feed.isOpened() or self.video_feed is None:
            raise InvalidCameraIndex

    async def read(self) -> AsyncGenerator[tuple[mediapipe.Image, int], None]:
        """
        Asynchronously yields frames from the webcam.

        Each iteration yields a tuple `(image, timestamp)`, where:
            - `image` is the captured frame converted to a `mediapipe.Image`.
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

    Attributes:
        video_source (VideoSource): The video feed which produces image frames.
        face_detector (FaceDetector): The face detector model object from MediaPipe.
        age_estimator (AgeEstimator): The age estimator model object.
        task_executor (TaskExecutor): Executor where tasks are submitted and
            offloaded to a thread.
    """

    _mode: VendingMode
    _strategies: dict[VendingMode, BaseVMCheckpoint]

    def __init__(
        self,
        video_source: VideoSource,
        face_detector: FaceDetector,
        age_estimator: AgeEstimator,
        task_executor: TaskExecutor,
    ) -> None:
        """
        Initializes the vending machine object and its dependencies.
        """
        self.video_source = video_source
        self.face_detector = face_detector
        self.age_estimator = age_estimator
        self.task_executor = task_executor

        self._lock = asyncio.Lock()
        self._metadata_obj = DetectionMetadata()
        self._mode = None  # ty: ignore[invalid-assignment]

        self.checkpoint_mapping = {
            VendingMode.CHECKPOINT_25: VMCheckpoint25(
                metadata_obj=self._metadata_obj,
            ),
            VendingMode.CHECKPOINT_50: VMCheckpoint50(
                metadata_obj=self._metadata_obj,
                age_estimator=self.age_estimator,
                task_executor=self.task_executor,
            ),
            VendingMode.CHECKPOINT_75: VMCheckpoint75(
                metadata_obj=self._metadata_obj,
                age_estimator=self.age_estimator,
                task_executor=self.task_executor,
            ),
        }

        self.full_system_handler = VMFullSystem(
            camera_feed=self.video_source.read,
            face_detector=None,  # ty: ignore[invalid-argument-type]
            age_estimator=self.age_estimator,
        )

    async def __aenter__(self) -> "VendingMachine":
        """Acquire the lock and return `self` upong entering the runtime context."""
        await self._lock.acquire()
        return self

    async def __aexit__(
        self, unused_exc_type, unused_exc_value, unused_traceback
    ) -> None:
        """
        Upon exiting the context manager:

        - Clear the recent frames queue from the checkpoint objects.
        - Reset values of the metadata object to `None`.
        - Release the lock.
        """
        if self._mode != VendingMode.FULL_SYSTEM:
            self.checkpoint_mapping[self._mode].recent_frames.clear()

        self._metadata_obj.clear()
        self._lock.release()

    @classmethod
    def create_default(cls) -> "VendingMachine":
        """Creates the vending machine object with default configuration."""
        vm = cls(
            video_source=VideoSource(),
            face_detector=None,  # ty: ignore[invalid-argument-type]
            age_estimator=AgeEstimator(
                weights_path=settings.AGE_ESTIMATOR_WEIGHTS_PATH
            ),
            task_executor=TaskExecutor(workers=2),
        )

        vm.face_detector = initialize_face_detector(
            model_asset_path=settings.FACE_DETECTOR_WEIGHTS_PATH_INFERENCE,
            result_callback=vm._result_callback,
        )

        return vm

    def set_mode(self, mode: VendingMode) -> None:
        if mode not in VendingMode:
            raise InvalidVendingMode

        self._mode = mode

    async def run_checkpoint(self) -> AsyncGenerator[DetectionMetadata, None]:
        """Entry point when running checkpoints."""
        async for image, timestamp_ms in self.video_source.read():
            self.face_detector.detect_async(image=image, timestamp_ms=timestamp_ms)
            yield self._metadata_obj

    async def simulate(self, websocket: WebSocket, db: AsyncDatabase) -> None:
        """
        Entry point for simulating the order process of the vending machine.

        Used in conjunction with `self.run` when vending machine is run with the mode
        full system.
        """
        await self.full_system_handler.simulate(websocket=websocket, db=db)

    async def run(self) -> AsyncGenerator[bytes, None]:
        """
        Entry point for the camera feed/stream with face detection.

        Used in conjunction with `self.simulate` when vending machine is run with the
        mode full system.
        """
        # Attach the face detector object on the full system handler just before running
        # since face detector is attached on the `VendingMachine` class after creation
        # and the handler is defined on its class creation.
        self.full_system_handler.face_detector = self.face_detector

        stream = self.full_system_handler.camera_stream()

        async for image in stream:
            image_bytes = None

            if image is not None:
                encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 70]

                _, buffer = cv2.imencode(".jpg", img=image, params=encode_params)
                image_bytes = buffer.tobytes()

            yield image_bytes

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

    def _result_callback(
        self,
        detection_result: DetectionResult,
        output_image: mediapipe.Image,
        timestamp_ms: int,
    ) -> None:
        """
        Callback function after a successful face detection.

        This callback will be attached on the `FaceDetector` object during
        instantiation.
        """
        image = output_image.numpy_view()
        self._metadata_obj.timestamp = timestamp_ms

        if self._mode == VendingMode.FULL_SYSTEM:
            self.full_system_handler.process(
                detection_result=detection_result,
                image=image,
                timestamp_ms=timestamp_ms,
            )
        else:
            self.checkpoint_mapping[self._mode].process(
                detection_result=detection_result,
                image=image,
                timestamp_ms=timestamp_ms,
            )
