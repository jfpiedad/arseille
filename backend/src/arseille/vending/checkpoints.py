from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import Future

import numpy as np
from mediapipe.tasks.python.components.containers.detections import DetectionResult

from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.services import get_current_weather
from arseille.vending.constants import FRAMES_LIMIT
from arseille.vending.data import DetectionMetadata
from arseille.vending.utils import TaskExecutor, annotate_image_with_bounding_box


class BaseVMCheckpoint(ABC):
    def __init__(
        self,
        metadata_obj: DetectionMetadata,
        age_estimator: AgeEstimator | None = None,
        task_executor: TaskExecutor | None = None,
    ) -> None:
        self.metadata_obj = metadata_obj
        self.age_estimator = age_estimator
        self.task_executor = task_executor

        self.recent_frames = deque([], maxlen=20)
        self.cancelled = False
        self.age_estimation_task_in_progress = False
        self.weather_task_in_progress = False

    @abstractmethod
    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        pass

    def age_estimator_task_callback(self, age_task: Future) -> None:
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
            self.metadata_obj.age = age_task.result()
        except Exception as exc:
            print(f"Age estimation task failed.\n {exc}")
            self.metadata_obj.age = None
        finally:
            self.age_estimation_task_in_progress = False

    def weather_task_callback(self, weather_task: Future) -> None:
        """Callback function after getting the get weather task/future is done."""

        try:
            self.metadata_obj.weather = weather_task.result()
        except Exception as exc:
            print(f"Getting weather data failed.\n {exc}")
            self.metadata_obj.weather = None
        finally:
            self.weather_task_in_progress = False

    def reset(self) -> None:
        """Reset some variables and object to its initial values."""
        self.metadata_obj.age = None
        self.recent_frames.clear()
        self.cancelled = True


class VMCheckpoint25(BaseVMCheckpoint):
    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            self.metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result
            )
        else:
            self.metadata_obj.annotated_image = image


class VMCheckpoint50(BaseVMCheckpoint):
    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            if self._is_submission_allowed():
                self.age_estimation_task_in_progress = True
                self.cancelled = False

                self.task_executor.add_task(
                    task_fn=self.age_estimator.predict,
                    done_callback=self.age_estimator_task_callback,
                    face_detection_data=list(self.recent_frames),
                )

            bounding_box = detection_result.detections[0].bounding_box

            self.recent_frames.append((bounding_box, image))
            self.metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image,
                detection_result=detection_result,
                age=self.metadata_obj.age,
            )
        else:
            self.metadata_obj.annotated_image = image
            self.reset()

    def _is_submission_allowed(self) -> None:
        """
        The submission of age estimator task to the executor is only allowed when:

        - The number of face detected frames is 20.
        - Age has not been calculated yet.
        - No age estimation task is in progress.
        """
        return (
            len(self.recent_frames) == FRAMES_LIMIT
            and self.metadata_obj.age is None
            and not self.age_estimation_task_in_progress
        )


class VMCheckpoint75(BaseVMCheckpoint):
    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            if self._is_submission_allowed():
                self.age_estimation_task_in_progress = True
                self.cancelled = False

                self.task_executor.add_task(
                    task_fn=self.age_estimator.predict,
                    done_callback=self.age_estimator_task_callback,
                    face_detection_data=list(self.recent_frames),
                )

                self.task_executor.add_task(
                    task_fn=get_current_weather,
                    done_callback=self.weather_task_callback,
                )

            bounding_box = detection_result.detections[0].bounding_box

            self.recent_frames.append((bounding_box, image))
            self.metadata_obj.annotated_image = annotate_image_with_bounding_box(
                image=image,
                detection_result=detection_result,
                age=self.metadata_obj.age,
            )
        else:
            self.metadata_obj.annotated_image = image
            self.reset()

    def _is_submission_allowed(self) -> None:
        """
        The submission of age estimator task and weather task to the executor is only
        allowed when:

        - The number of face detected frames is 20.
        - Age has not been calculated yet.
        - No age estimation task is in progress.
        - No weather task is in progress.
        """
        return (
            len(self.recent_frames) == FRAMES_LIMIT
            and self.metadata_obj.age is None
            and not self.age_estimation_task_in_progress
            and not self.weather_task_in_progress
        )


class VMFullSystem(BaseVMCheckpoint):
    pass
