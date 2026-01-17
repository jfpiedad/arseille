import asyncio
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import Future
from typing import Any, AsyncGenerator, Callable

import mediapipe
import numpy as np
from fastapi import WebSocket
from mediapipe.tasks.python.components.containers.detections import DetectionResult
from mediapipe.tasks.python.vision.face_detector import FaceDetector
from pymongo.asynchronous.database import AsyncDatabase

from arseille.ml_models.age_estimation.inference import AgeEstimator
from arseille.vending.constants import FRAMES_LIMIT
from arseille.vending.data import (
    DetectionData,
    DetectionMetadata,
    InboundMessage,
    OutboundMessage,
)
from arseille.vending.enums import InboundInstruction, OutboundInstruction, Weather
from arseille.vending.schemas import TransactionCreate
from arseille.vending.services import create_transaction_in_db, get_current_weather
from arseille.vending.utils import (
    TaskExecutor,
    annotate_image_with_bounding_box,
    determine_age_group,
)


class BaseVMCheckpoint(ABC):
    """
    Abstract vending machine checkpoint class.

    Defines the callbacks of age estimator task and weather task that are submitted
    in the ThreadPoolExecutor. It also defines a helper method and common variables used
    in the concrete classes.

    Attributes:
        metadata_obj (DetectionMetadata): The reference of the metadata object
            instantiated on the vending machine class.
        age_estimator (AgeEstimator, optional): The age estimator model object.
        task_executor (TaskExecutor, optional): Executor where tasks are submitted and
            offloaded to a thread.
        recent_frames (deque): A queue that stores the frames of the recent detection
            results. The max length of the queue is `20`.
    """

    def __init__(
        self,
        metadata_obj: DetectionMetadata,
        age_estimator: AgeEstimator | None = None,
        task_executor: TaskExecutor | None = None,
    ) -> None:
        self.metadata_obj = metadata_obj
        self.age_estimator = age_estimator
        self.task_executor = task_executor
        self.recent_frames = deque([], maxlen=FRAMES_LIMIT)

        self._cancelled = False
        self._age_estimation_task_in_progress = False
        self._weather_task_in_progress = False

    @abstractmethod
    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        pass

    def _age_estimator_task_callback(self, age_task: Future) -> None:
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
            self._age_estimation_task_in_progress = False
            return

        try:
            self.metadata_obj.age = age_task.result()
        except Exception:
            self.metadata_obj.age = None
            raise
        finally:
            self._age_estimation_task_in_progress = False

    def _weather_task_callback(self, weather_task: Future) -> None:
        """Callback function after getting the get weather task/future is done."""

        try:
            self.metadata_obj.weather = weather_task.result()
        except Exception:
            self.metadata_obj.weather = None
            raise
        finally:
            self._weather_task_in_progress = False

    def _reset(self) -> None:
        """Reset some variables and object to its initial values."""
        self.metadata_obj.age = None
        self.recent_frames.clear()
        self._cancelled = True


class VMCheckpoint25(BaseVMCheckpoint):
    """Vending machine 25 percent checkpoint."""

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
    """Vending machine 50 percent checkpoint."""

    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            if self._is_submission_allowed():
                self._age_estimation_task_in_progress = True
                self._cancelled = False

                self.task_executor.add_task(  # type: ignore[possibly-missing-attribute]
                    task_fn=self.age_estimator.predict,  # type: ignore[possibly-missing-attribute]
                    done_callback=self._age_estimator_task_callback,
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
            self._reset()

    def _is_submission_allowed(self) -> bool:
        """
        The submission of age estimator task to the executor is only allowed when:

        - The number of face detected frames is 20.
        - Age has not been calculated yet.
        - No age estimation task is in progress.
        """
        return (
            len(self.recent_frames) == FRAMES_LIMIT
            and self.metadata_obj.age is None
            and not self._age_estimation_task_in_progress
        )


class VMCheckpoint75(BaseVMCheckpoint):
    """Vending machine 75 percent checkpoint."""

    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            if self._is_submission_allowed():
                self._age_estimation_task_in_progress = True
                self._cancelled = False

                self.task_executor.add_task(  # type: ignore[possibly-missing-attribute]
                    task_fn=self.age_estimator.predict,  # type: ignore[possibly-missing-attribute]
                    done_callback=self._age_estimator_task_callback,
                    face_detection_data=list(self.recent_frames),
                )

                self.task_executor.add_task(  # type: ignore[possibly-missing-attribute]
                    task_fn=get_current_weather,
                    done_callback=self._weather_task_callback,
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
            self._reset()

    def _is_submission_allowed(self) -> bool:
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
            and not self._age_estimation_task_in_progress
            and not self._weather_task_in_progress
        )


class VMFullSystem:
    """
    Vending machine full system.

    This behaves differently with checkpoints as now user interaction is included to
    order a drink from the vending machine.

    Attributes:
        camera_feed (Callable[[], AsyncGenerator[tuple[mediapipe.Image, int], None]]):
            The function reference of `VideoSource.read()` which is an async generator.
        face_detector (FaceDetector): The face detector model object from MediaPipe.
            Reference object from the main vending machine class.
        age_estimator (AgeEstimator): The age estimator model object.
            Reference object from the main vending machine class.
    """

    _image: np.ndarray
    _websocket: WebSocket

    def __init__(
        self,
        camera_feed: Callable[[], AsyncGenerator[tuple[mediapipe.Image, int], None]],
        face_detector: FaceDetector,
        age_estimator: AgeEstimator,
    ) -> None:
        self.camera_feed = camera_feed
        self.face_detector = face_detector
        self.age_estimator = age_estimator

        self._image = None  # ty: ignore[invalid-assignment]
        self._websocket = None  # ty: ignore[invalid-assignment]
        self._recent_frames = deque([], maxlen=FRAMES_LIMIT)

        # Flag indicating if the vending machine is currently in order process.
        # This is set to `True` when user decides to order a drink.
        self._currently_ordering = False

        # Flag to signal the detection process to start processing the user.
        self._start_ordering = False
        self._event = asyncio.Event()

    def process(
        self, detection_result: DetectionResult, image: np.ndarray, timestamp_ms: int
    ) -> None:
        if detection_result.detections:
            if self._start_ordering and len(self._recent_frames) == 20:
                self._currently_ordering = True
                self._event.set()

            bounding_box = detection_result.detections[0].bounding_box

            self._recent_frames.append((bounding_box, image))
            self._image = annotate_image_with_bounding_box(
                image=image, detection_result=detection_result
            )
        else:
            self._recent_frames.clear()
            self._image = image

    async def simulate(self, websocket: WebSocket, db: AsyncDatabase) -> None:
        self._websocket = websocket

        # Make sure the variables are in initial state as it may have been changed
        # previously.
        self._reset()

        # Initial signal indicating the frontend is ready to begin simulation.
        await self._websocket.receive_text()

        await self._send(msg_type=OutboundInstruction.RESET)

        async for message in self._receive():
            if message.type == InboundInstruction.START_ORDER:
                # Message frotnend to wait while its processing the user.
                await self._send(msg_type=OutboundInstruction.PROCESSING_USER)

                self._start_ordering = True

                try:
                    await asyncio.wait_for(self._event.wait(), timeout=5.0)

                    age, weather = await asyncio.to_thread(self._calculate)
                    age_group = determine_age_group(age=age)

                    detection_data = DetectionData(
                        age=age, age_group=age_group, weather=weather
                    )

                    await self._send(
                        msg_type=OutboundInstruction.DISPLAY_DRINKS,
                        detection_data=detection_data.model_dump(by_alias=True),
                    )
                except asyncio.TimeoutError:
                    self._event.clear()
                    self._reset()

                    await self._send(msg_type=OutboundInstruction.RESET)
            elif message.type == InboundInstruction.VEND:
                # Message frontend to wait while the drink is being prepared.
                await self._send(msg_type=OutboundInstruction.PREPARING_DRINK)

                # Save transaction data to database. The time it takes to save the data
                # will be used to mimic the time in preparing the drink.
                # Note: TOO FAST!
                transaction_data = TransactionCreate(**message.transaction_data)  # ty: ignore[invalid-argument-type]
                await create_transaction_in_db(db=db, transaction_data=transaction_data)

                await self._send(msg_type=OutboundInstruction.DRINK_READY)
            elif message.type == InboundInstruction.TAKE_DRINK:
                self._reset()
                await self._send(msg_type=OutboundInstruction.RESET)
            elif message.type == InboundInstruction.CANCEL:
                self._reset()
                await self._send(msg_type=OutboundInstruction.RESET)
            else:
                raise ValueError(f"Unknown message type {message.type}")

    async def camera_stream(self) -> AsyncGenerator[mediapipe.Image, None]:
        """
        Asynchronous generator that yields an image from the webcam.
        """
        async for image, timestamp_ms in self.camera_feed():
            if not self._currently_ordering:
                self.face_detector.detect_async(image=image, timestamp_ms=timestamp_ms)
            else:
                image = image.numpy_view()
                self._image = image

            yield self._image

    async def _receive(self) -> AsyncGenerator[InboundMessage, None]:
        """
        Wrapper for `websocket.iter_json()` which deserializes json data to
        `InboundMessage`.
        """
        async for data in self._websocket.iter_json():
            yield InboundMessage(**data)

    async def _send(
        self,
        msg_type: OutboundInstruction,
        detection_data: dict[str, Any] | None = None,
    ) -> None:
        message = OutboundMessage(type=msg_type)

        if detection_data is not None:
            message.detection_data = detection_data

        await self._websocket.send_json(data=message.model_dump(by_alias=True))

    def _calculate(self) -> tuple[int, Weather]:
        """Calculate age of the user and determine the current weather conditions."""
        age = self.age_estimator.predict(face_detection_data=list(self._recent_frames))
        weather = get_current_weather()

        return age, weather

    def _reset(self) -> None:
        """Reset some variables and object to its initial values."""
        self._recent_frames.clear()
        self._currently_ordering = False
        self._start_ordering = False
        self._event.clear()
