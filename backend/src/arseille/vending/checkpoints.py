from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import Future
from functools import partial

import numpy as np
from mediapipe.tasks.python.components.containers.detections import DetectionResult

from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.services import get_current_weather
from arseille.vending.constants import FRAMES_LIMIT
from arseille.vending.data import DetectionMetadata
from arseille.vending.utils import TaskExecutor, annotate_image_with_bounding_box


class TaskMixin:
    """
    Mixin providing callback to age estimator task and weather task. It also
    provides variables and some helper functions.
    """

    def __init__(self) -> None:
        self.recent_detection_results = deque([], maxlen=FRAMES_LIMIT)
        self.cancelled = False
        self.age_estimation_task_in_progress = False
        self.weather_task_in_progress = False

    def is_submission_allowed(self, metadata_obj: DetectionMetadata) -> bool:
        """Helper method which does multiple boolean checks."""
        if len(self.recent_detection_results) != FRAMES_LIMIT:
            return False

        if metadata_obj.age is not None:
            return False

        if self.age_estimation_task_in_progress:
            return False

        return True

    def reset(self, metadata_obj: DetectionMetadata) -> None:
        """Reset some variables and object to its initial values."""
        metadata_obj.age = None
        self.recent_detection_results.clear()
        self.cancelled = True

    def age_estimator_task_callback(
        self, metadata_obj: DetectionMetadata, age_task: Future
    ) -> None:
        """Callback function after the age estimation task/future is done."""

        if self.cancelled:
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
            self.age_estimation_task_in_progress = False
            return

        try:
            metadata_obj.age = age_task.result()
        except Exception as exc:
            print(f"Age estimation task failed.\n {exc}")
            metadata_obj.age = None
        finally:
            self.age_estimation_task_in_progress = False

    def weather_task_callback(
        self, metadata_obj: DetectionMetadata, weather_task: Future
    ) -> None:
        """Callback function after getting the get weather task/future is done."""

        try:
            metadata_obj.weather = weather_task.result()
        except Exception as exc:
            print(f"Getting weather data failed.\n {exc}")
            metadata_obj.weather = None
        finally:
            self.weather_task_in_progress = False


class BaseCheckpoint(ABC):
    """Abstract class for different checkpoints of the vending machine."""

    @abstractmethod
    def process(
        self,
        metadata_obj: DetectionMetadata,
        detection_result: DetectionResult,
        image: np.ndarray,
        age_estimator: AgeEstimator,
        executor: TaskExecutor,
    ) -> None:
        pass


class Checkpoint25Percent(BaseCheckpoint):
    def process(
        self,
        metadata_obj: DetectionMetadata,
        detection_result: DetectionResult,
        image: np.ndarray,
        age_estimator: AgeEstimator,
        executor: TaskExecutor,
    ) -> None:
        if detection_result.detections:
            metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result
            )
        else:
            metadata_obj.annotated_image = image


class Checkpoint50Percent(BaseCheckpoint, TaskMixin):
    def process(
        self,
        metadata_obj: DetectionMetadata,
        detection_result: DetectionResult,
        image: np.ndarray,
        age_estimator: AgeEstimator,
        executor: TaskExecutor,
    ) -> None:
        if detection_result.detections:
            if self.is_submission_allowed(metadata_obj=metadata_obj):
                self.age_estimation_task_in_progress = True
                self.cancelled = False

                executor.add_task(
                    task_fn=age_estimator.predict,
                    done_callback=partial(
                        self.age_estimator_task_callback, metadata_obj
                    ),
                    face_detection_data=list(self.recent_detection_results),
                )

            bounding_box = detection_result.detections[0].bounding_box

            self.recent_detection_results.append((bounding_box, image))
            metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result, age=metadata_obj.age
            )
        else:
            metadata_obj.annotated_image = image
            self.reset(metadata_obj=metadata_obj)


class Checkpoint75Percent(BaseCheckpoint, TaskMixin):
    def process(
        self,
        metadata_obj: DetectionMetadata,
        detection_result: DetectionResult,
        image: np.ndarray,
        age_estimator: AgeEstimator,
        executor: TaskExecutor,
    ) -> None:
        if detection_result.detections:
            if self.is_submission_allowed(metadata_obj=metadata_obj):
                self.age_estimation_task_in_progress = True
                self.cancelled = False

                executor.add_task(
                    task_fn=age_estimator.predict,
                    done_callback=partial(
                        self.age_estimator_task_callback, metadata_obj
                    ),
                    face_detection_data=list(self.recent_detection_results),
                )

                executor.add_task(
                    task_fn=get_current_weather,
                    done_callback=partial(self.weather_task_callback, metadata_obj),
                )

            bounding_box = detection_result.detections[0].bounding_box

            self.recent_detection_results.append((bounding_box, image))
            metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result, age=metadata_obj.age
            )
        else:
            metadata_obj.annotated_image = image
            self.reset(metadata_obj=metadata_obj)

    def is_submission_allowed(self, metadata_obj: DetectionMetadata) -> bool:
        is_allowed = super().is_submission_allowed(metadata_obj)

        if not is_allowed:
            return False

        if self.weather_task_in_progress:
            return False

        return True
