import json
import struct
import time
from concurrent.futures import Executor, Future
from functools import lru_cache
from random import randint
from typing import Any, AsyncGenerator, Callable, TypedDict

import cv2
import mediapipe
import numpy as np
from fastapi import WebSocketDisconnect
from mediapipe.tasks.python.components.containers.bounding_box import BoundingBox
from mediapipe.tasks.python.components.containers.category import Category
from mediapipe.tasks.python.components.containers.detections import (
    Detection,
    DetectionResult,
)

from arseille.config import settings
from arseille.vending.enums import Weather
from arseille.vending.utils import TaskExecutor
from arseille.vending.vending_machine import VendingMachine

HEADER_BYTE = 4


class MetadataDict(TypedDict):
    age: int | None
    weather: Weather | None
    timestamp: int | None


def create_random_detection_result() -> DetectionResult:
    detections = []

    for _ in range(3):
        bounding_box = BoundingBox(
            origin_x=randint(100, 200),
            origin_y=randint(100, 200),
            width=randint(100, 300),
            height=randint(100, 300),
        )

        detection = Detection(bounding_box=bounding_box, categories=[Category()])
        detections.append(detection)

    return DetectionResult(detections=detections)


def unpack_vending_stream_data(data: bytes) -> tuple[int, MetadataDict, np.ndarray]:
    """Unpacks the bytes sent by the vending machine websocket endpoint."""
    header = data[:4]

    metadata_length = struct.unpack("<I", header)[0]
    unpacked_metadata = json.loads(data[4 : 4 + metadata_length])
    unpacked_image = data[4 + metadata_length :]

    unpacked_image = np.frombuffer(unpacked_image, dtype=np.uint8)

    return metadata_length, unpacked_metadata, unpacked_image


@lru_cache
def create_dummy_vending_machine() -> VendingMachine:
    vm = DummyVendingMachine(
        video_source=DummyVideoSource(),
        face_detector=None,
        age_estimator=DummyAgeEstimator(),
        task_executor=TaskExecutor(executor=DummyExecutor()),
    )

    face_detector = DummyFaceDetector()
    face_detector.callback = vm._result_callback
    vm.face_detector = face_detector

    return vm


class DummyVendingMachine(VendingMachine):
    async def __aenter__(self) -> "DummyVendingMachine":
        await super().__aenter__()
        DummyFaceDetector._RAISE_WEBSOCKET_DISCONNECT = False
        return self


class DummyExecutor(Executor):
    """
    Dummy executor.

    Works like a ThreadPoolExecutor but tasks are executed
    synchronously instead of offloading it to another thread.
    """

    def __init__(self) -> None:
        self._shutdown = False

    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        if self._shutdown:
            raise RuntimeError("Cannot schedule new futures after shutdown.")

        future = Future()
        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except BaseException as exc:
            future.set_exception(exc)

        return future

    def shutdown(self, wait: bool = True) -> None:
        self._shutdown = True


class DummyVideoSource:
    """
    Dummy video source.

    The `read()` function returns the same exact frame from a static image.
    """

    def __init__(self) -> None:
        image = cv2.imread(
            str(settings.ROOT_DIRECTORY / "backend" / "tests" / "kimshin.png")
        )
        self.image = image

    async def read(self) -> AsyncGenerator[tuple[mediapipe.Image, int], None]:
        while True:
            timestamp_ms = int(round(time.time() * 1000))
            image = mediapipe.Image(
                image_format=mediapipe.ImageFormat.SRGB, data=self.image
            )

            yield image, timestamp_ms

    def close(self) -> None:
        pass


class DummyFaceDetector:
    """
    Dummy face detector model.

    The `detect_async()` function works synchronously and returns a fake
    detection result.
    """

    # This variable is used to raise the exception WebSocketDisconnect during testing.
    # Since checkpoints is continouosly sending data to the browser, it has no way of
    # knowing if a close frame is sent from the browser. It relies on receive_bytes()
    # function to fail as soon as the tab is closed since the underlying TCP socket
    # will be closed in which it raises WebSocketDisconnect and disconnects the
    # connection. During testing, there's no TCP socket involved, so receive_bytes()
    # will never fail, so I added this flag so that I have a way of disconnecting the
    # connection which will prevent hanging the test suite. This is a hacky way but
    # maybe I'll figure out something in the future.
    _RAISE_WEBSOCKET_DISCONNECT = False

    def __init__(self) -> None:
        self.callback = None

    def detect_async(
        self,
        image: mediapipe.Image,
        timestamp_ms: int,
    ) -> None:
        if self._RAISE_WEBSOCKET_DISCONNECT:
            raise WebSocketDisconnect(code=1006)

        detection_result = create_random_detection_result()

        self.callback(detection_result, image, timestamp_ms)

    def close(self) -> None:
        pass


class DummyAgeEstimator:
    """
    Dummy age estimator model.

    The `predict()` function always returns the age 25.
    """

    def predict(self, face_detection_data: list[tuple[BoundingBox, np.ndarray]]) -> int:
        return 25
