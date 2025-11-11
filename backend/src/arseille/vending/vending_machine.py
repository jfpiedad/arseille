import asyncio
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import AsyncGenerator, TypedDict

import mediapipe
import numpy as np
from cv2 import VideoCapture
from mediapipe.tasks.python.components.containers.bounding_box import BoundingBox
from mediapipe.tasks.python.components.containers.detections import DetectionResult

from arseille.enums import Weather
from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.ml_models.face_detection.inference import initialize_face_detector
from arseille.services import get_current_weather
from arseille.vending.utils import (
    annotate_image_with_bounding_box,
)


class VendingMode(Enum):
    CHECKPOINT_25 = 1
    CHECKPOINT_50 = 2
    CHECKPOINT_75 = 3
    FULL = 4


class DetectionMetadata(TypedDict):
    age: int
    weather: Weather


class VendingMachine:
    """
    The vending machine has 4 modes based on requirement. The machine is designed to
    only process one user at a time just like how a real vending machine would.

    **Mode 1: Checkpoint 25**

    - Detects face on each frame and draws a bounding box if its detected.

    **Mode 2: Checkpoint 50**

    - Detects face on each frame and if a face is detected, its data is passed to the
    age estimation model. The age estimation model only runs when the number of frames
    with face detected is equal to 20 to do averaging and trimming to rule out false
    positives.

    **Mode 3: Checkpoint 75**

    - Essentially the same as `Mode 2` but with added current weather data that is
    determined through a Third-party API.

    **Mode 4: Full System**

    - ...
    """

    _CAMERA_INDEX = 0
    _FRAMES_LIMIT = 20

    _recent_face_detection_results: deque[tuple[BoundingBox, np.ndarray]]
    age: int
    weather: Weather
    annotated_image: np.ndarray

    def __init__(self) -> None:
        self.face_detector = initialize_face_detector(callback=self._detection_callback)
        self.age_estimator = AgeEstimator()

        self._video_feed = self._initialize_video_source()

        self._mode = VendingMode.FULL

        # Lock to make sure only one vending machine is running at a time.
        self._lock = asyncio.Lock()

        self._recent_face_detection_results = deque([], maxlen=self._FRAMES_LIMIT)

        # Since the callback function for mediapipe's `detect_async()` function cannot
        # be made async, sync functions are offloaded into a threadpool to make it
        # non-blocking and not block the entire event loop.
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._age_estimation_in_progress = False
        self._weather_in_progress = False

        # Boolean flag to indicate if age estimation results is stale.
        self._cancelled = False

        self.age = None
        self.weather = None
        self.annotated_image = None

    @property
    def detection_metadata(self) -> DetectionMetadata:
        return {"age": self.age, "weather": self.weather}

    def release_resources(self) -> None:
        """
        Release the following resources:

        - Face detector's task runner (mediapipe vision task instance).
        - OpenCV's VideoCapture
        - ThreadPoolExecutor
        """

        self.face_detector.close()
        self._video_feed.release()
        self._executor.shutdown(wait=True)

    async def read_frame_from_webcam(
        self,
    ) -> AsyncGenerator[tuple[mediapipe.Image, int], None]:
        """
        Generator that yields 2-tuple `(mediapipe.Image, timestamp)`, where each image
        is a converted opencv frame and the timestamp marks its capture."
        """

        while True:
            success, frame = await asyncio.to_thread(self._video_feed.read)

            if not success:
                print("Could not read frame.")
                break

            timestamp_ms = int(round(time.time() * 1000))

            image = mediapipe.Image(image_format=mediapipe.ImageFormat.SRGB, data=frame)

            yield image, timestamp_ms

    def set_mode(self, mode: VendingMode) -> None:
        self._mode = mode

    def get_mode(self) -> VendingMode:
        return self._mode

    async def set_unavailable(self) -> None:
        await self._lock.acquire()

    def set_available(self) -> None:
        self._lock.release()

    def _initialize_video_source(self) -> VideoCapture:
        """Initialize video source with OpenCV's `VideoCapture` object."""

        video_feed = VideoCapture(self._CAMERA_INDEX)

        if video_feed is None or not video_feed.isOpened():
            raise RuntimeError(
                f"Failed to open video source with index {self._CAMERA_INDEX}"
            )

        return video_feed

    def _detection_callback(
        self,
        detection_result: DetectionResult,
        output_image: mediapipe.Image,
        timestamp_ms: int,
    ) -> None:
        """Callback function after calling `detect_async()` from FaceDetector object."""

        image = output_image.numpy_view()

        if self._mode == VendingMode.CHECKPOINT_25:
            self._process_checkpoint_25(detection_result=detection_result, image=image)
        elif self._mode == VendingMode.CHECKPOINT_50:
            self._process_checkpoint_50(detection_result=detection_result, image=image)
        elif self._mode == VendingMode.CHECKPOINT_75:
            self._process_checkpoint_75(detection_result=detection_result, image=image)
        elif self._mode == VendingMode.FULL:
            self._process_full_system(detection_result=detection_result, image=image)
        else:
            raise ValueError(f"Vending machine is set on an unknown mode {self._mode}")

    def _process_checkpoint_25(
        self, detection_result: DetectionResult, image: np.ndarray
    ) -> None:
        if detection_result.detections:
            self.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result
            )
        else:
            self.annotated_image = image

    def _process_checkpoint_50(
        self, detection_result: DetectionResult, image: np.ndarray
    ) -> None:
        if detection_result.detections:
            if (
                self.age is None
                and not self._age_estimation_in_progress
                and len(self._recent_face_detection_results) == self._FRAMES_LIMIT
            ):
                self._age_estimation_in_progress = True
                self._cancelled = False

                data = list(self._recent_face_detection_results)

                age_task = self._executor.submit(self.age_estimator.predict, data)
                age_task.add_done_callback(self._age_estimator_callback)

            bounding_box = detection_result.detections[0].bounding_box

            self._recent_face_detection_results.append((bounding_box, image))
            self.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result, age=self.age
            )
        else:
            self.annotated_image = image
            self.age = None
            self._recent_face_detection_results.clear()
            self._cancelled = True

    def _process_checkpoint_75(
        self, detection_result: DetectionResult, image: np.ndarray
    ) -> None:
        if detection_result.detections:
            if (
                self.age is None
                and not (self._age_estimation_in_progress or self._weather_in_progress)
                and len(self._recent_face_detection_results) == self._FRAMES_LIMIT
            ):
                self._age_estimation_in_progress = True
                self._cancelled = False

                data = list(self._recent_face_detection_results)

                age_task = self._executor.submit(self.age_estimator.predict, data)
                age_task.add_done_callback(self._age_estimator_callback)

                self._weather_in_progress = True

                weather_task = self._executor.submit(get_current_weather)
                weather_task.add_done_callback(self._weather_callback)

            bounding_box = detection_result.detections[0].bounding_box

            self._recent_face_detection_results.append((bounding_box, image))
            self.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result, age=self.age
            )
        else:
            self.annotated_image = image
            self.age = None
            self._recent_face_detection_results.clear()
            self._cancelled = True

    def _process_full_system(self) -> None:
        pass

    def _age_estimator_callback(self, age_task: Future) -> None:
        """Callback function after the age estimation task/future is done."""

        if self._cancelled:
            # If the flag is True, it means the result of this callback is stale.
            # This flag is used to prevent a race condition that may possibly result
            # a stale data.
            # SCENARIO:
            # Person 1 shows his face on the camera, and immediately after the age
            # estimation task is submitted to the executor, Person 1 moves out of the
            # camera view, and since there's no face detected, `self.age` is set to None
            # before the task is even finished. Then Person 2 shows his face on the
            # camera and since the callback is probably finished this time, the age
            # shown is actually the age of Person 1. Though this scenario is an extreme
            # edge case and is prone to happening on slower systems.
            self._age_estimation_in_progress = False
            return

        try:
            self.age = age_task.result()
        except Exception as exc:
            print(f"Age estimation task failed. \n Details: {exc}")
            self.age = None
        finally:
            self._age_estimation_in_progress = False

    def _weather_callback(self, weather_task: Future) -> None:
        """Callback function after getting the current weather data is done."""

        try:
            self.weather = weather_task.result()
        except Exception as exc:
            print(f"Getting weather data failed. \n Details: {exc}")
            self.weather = None
        finally:
            self._weather_in_progress = False
