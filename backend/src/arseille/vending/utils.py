import asyncio
import json
import struct
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import cv2
import numpy as np
from mediapipe.tasks.python.components.containers.detections import DetectionResult

from arseille.vending.constants import (
    BGR_GREEN,
    BGR_YELLOW,
    BOX_THICKNESS,
    FONT_SIZE,
    FONT_THICKNESS,
    MARGIN,
)


def sort_detection_results_desc(detection_result: DetectionResult) -> None:
    """
    Sorts the detection results inplace in descending order based on the area of the
    bounding box.
    """

    detection_result.detections.sort(
        key=lambda detection: detection.bounding_box.width
        * detection.bounding_box.height,
        reverse=True,
    )


def annotate_image_with_bounding_box(
    image: np.ndarray, detection_result: DetectionResult, age: int | None = None
) -> np.ndarray:
    """Annotate image with bounding box and age label."""

    # Sort detections if there are more than 1.
    if len(detection_result.detections) > 1:
        sort_detection_results_desc(detection_result=detection_result)

    image_copy = image.copy()

    for index, detection in enumerate(detection_result.detections):
        bounding_box = detection.bounding_box

        start_point = (bounding_box.origin_x, bounding_box.origin_y)
        end_point = (
            bounding_box.origin_x + bounding_box.width,
            bounding_box.origin_y + bounding_box.height,
        )

        if index == 0:
            box_color = BGR_GREEN
        else:
            box_color = BGR_YELLOW

        cv2.rectangle(
            img=image_copy,
            pt1=start_point,
            pt2=end_point,
            color=box_color,
            thickness=BOX_THICKNESS,
        )

    # If age is given, add the necessary label.
    if age is not None:
        bounding_box = detection_result.detections[0].bounding_box

        text_location = (bounding_box.origin_x, bounding_box.origin_y - MARGIN)

        cv2.putText(
            img=image_copy,
            text=str(age),
            org=text_location,
            fontFace=cv2.FONT_HERSHEY_PLAIN,
            fontScale=FONT_SIZE,
            color=BGR_GREEN,
            thickness=FONT_THICKNESS,
        )

    return image_copy


def concatenate_image_and_metadata(
    metadata: dict[str, Any], image: np.ndarray
) -> bytes:
    """
    Convert metadata and image to bytes and concatenate them into a
    single binary message.
    """

    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 70]

    _, buffer = cv2.imencode(".jpg", img=image, params=encode_params)
    image_bytes = buffer.tobytes()

    metadata_bytes = json.dumps(metadata).encode("utf-8")

    # Create 4-byte header (unsigned int, little-endian)
    # This stores the length of the metadata
    header = struct.pack("<I", len(metadata_bytes))

    return b"".join([header, metadata_bytes, image_bytes])


class TaskExecutor:
    """
    Executor where tasks are submitted and invokes the corresponding callback function
    after the task is finished.

    Uses `ThreadPoolExecutor`.
    """

    def __init__(
        self, executor: ThreadPoolExecutor | None = None, workers: int = 2
    ) -> None:
        if executor is None:
            self.executor = ThreadPoolExecutor(max_workers=workers)
        else:
            self.executor = executor

    def add_task(
        self,
        task_fn: Callable[..., Any],
        done_callback: Callable[[asyncio.Future], None],
        **kwargs,
    ) -> None:
        """
        Submits a task to the executor.

        Args:
            task_fn (Callable[..., Any]): The function that will be submitted and
             executed through the executor.
            done_callback (Callable[[asyncio.Future], None]): The callback function
             after `task_fn` is done executing.
        """
        task = self.executor.submit(task_fn, **kwargs)
        task.add_done_callback(done_callback)

    def shutdown(self) -> None:
        """Shuts down the executor and wait for it to finish."""
        self.executor.shutdown(wait=True)
