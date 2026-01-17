from concurrent.futures import Future

import cv2
import numpy as np
import pytest
from mediapipe.tasks.python.components.containers.bounding_box import BoundingBox
from mediapipe.tasks.python.components.containers.category import Category
from mediapipe.tasks.python.components.containers.detections import (
    Detection,
    DetectionResult,
)

from arseille.config import settings
from arseille.vending.constants import BGR_GREEN, BGR_YELLOW, BOX_THICKNESS
from arseille.vending.utils import (
    TaskExecutor,
    annotate_image_with_bounding_box,
    concatenate_image_and_metadata,
    sort_detection_results_desc,
)
from tests.utils import (  # ty: ignore[unresolved-import]
    DummyExecutor,
    unpack_vending_stream_data,
)

TEST_IMAGE_WIDTH = 693
TEST_IMAGE_HEIGHT = 653


@pytest.fixture
def image() -> np.ndarray:
    image = cv2.imread(
        str(settings.ROOT_DIRECTORY / "backend" / "tests" / "kimshin.png")
    )
    return image


@pytest.fixture
def single_detection() -> DetectionResult:
    bounding_box = BoundingBox(
        origin_x=100,
        origin_y=100,
        width=300,
        height=300,
    )

    detection = Detection(bounding_box=bounding_box, categories=[Category()])

    return DetectionResult(detections=[detection])


@pytest.fixture
def multiple_detection() -> DetectionResult:
    detections = []

    for index in range(1, 4):
        bounding_box = BoundingBox(
            origin_x=100 * index,
            origin_y=100,
            width=40 * index,
            height=40 * index,
        )

        detection = Detection(bounding_box=bounding_box, categories=[Category()])
        detections.append(detection)

    return DetectionResult(detections=detections)


def test_sort_detection_results_desc(multiple_detection: DetectionResult) -> None:
    detection_result = multiple_detection

    sort_detection_results_desc(detection_result=detection_result)

    detections = detection_result.detections

    for index in range(len(detections) - 1):
        first_bbox = detections[index].bounding_box
        first_bbox_area = first_bbox.width * first_bbox.height

        second_bbox = detections[index + 1].bounding_box
        second_bbox_area = second_bbox.width * second_bbox.height

        assert first_bbox_area >= second_bbox_area


def test_annotate_image_with_bounding_box_single_detection(
    image: np.ndarray, single_detection: DetectionResult
) -> None:
    detection_result = single_detection

    annotated_image = annotate_image_with_bounding_box(
        image=image, detection_result=detection_result
    )

    # Check if a copy of the image was made
    assert annotated_image is not image

    bounding_box = detection_result.detections[0].bounding_box
    origin_x = bounding_box.origin_x
    origin_y = bounding_box.origin_y
    width = bounding_box.width
    height = bounding_box.height

    # Checks the top-edge -> right-edge -> bottom-edge -> left-edge
    assert np.all(annotated_image[origin_y, origin_x : origin_x + width] == BGR_GREEN)
    assert np.all(
        annotated_image[origin_y : origin_y + height, origin_x + width] == BGR_GREEN
    )
    assert np.all(
        annotated_image[origin_y + height, origin_x : origin_x + width] == BGR_GREEN
    )
    assert np.all(annotated_image[origin_y : origin_y + height, origin_x] == BGR_GREEN)

    # Interior of the bounding box
    annotated_interior = annotated_image[
        origin_y + BOX_THICKNESS : origin_y + height - BOX_THICKNESS,
        origin_x + BOX_THICKNESS : origin_x + width - BOX_THICKNESS,
    ]
    original_interior = image[
        origin_y + BOX_THICKNESS : origin_y + height - BOX_THICKNESS,
        origin_x + BOX_THICKNESS : origin_x + width - BOX_THICKNESS,
    ]

    assert np.array_equal(annotated_interior, original_interior)


def test_annotate_image_with_bounding_box_multiple_detection(
    image: np.ndarray, multiple_detection: DetectionResult
) -> None:
    detection_result = multiple_detection

    annotated_image = annotate_image_with_bounding_box(
        image=image, detection_result=detection_result
    )

    # Check if a copy of the image was made
    assert annotated_image is not image

    for index, detection in enumerate(detection_result.detections):
        if index == 0:
            pixel_color = BGR_GREEN
        else:
            pixel_color = BGR_YELLOW

        bounding_box = detection.bounding_box
        origin_x = bounding_box.origin_x
        origin_y = bounding_box.origin_y
        width = bounding_box.width
        height = bounding_box.height

        # Checks the top-edge -> right-edge -> bottom-edge -> left-edge
        assert np.all(
            annotated_image[origin_y, origin_x : origin_x + width] == pixel_color
        )
        assert np.all(
            annotated_image[origin_y : origin_y + height, origin_x + width]
            == pixel_color
        )
        assert np.all(
            annotated_image[origin_y + height, origin_x : origin_x + width]
            == pixel_color
        )
        assert np.all(
            annotated_image[origin_y : origin_y + height, origin_x] == pixel_color
        )

        # Interior of the bounding box
        annotated_interior = annotated_image[
            origin_y + BOX_THICKNESS : origin_y + height - BOX_THICKNESS,
            origin_x + BOX_THICKNESS : origin_x + width - BOX_THICKNESS,
        ]
        original_interior = image[
            origin_y + BOX_THICKNESS : origin_y + height - BOX_THICKNESS,
            origin_x + BOX_THICKNESS : origin_x + width - BOX_THICKNESS,
        ]

        assert np.array_equal(annotated_interior, original_interior)


def test_concatenate_image_and_metadata(image: np.ndarray) -> None:
    metadata = {"Ebon Knight": "Ishmelga"}

    concatenated_data = concatenate_image_and_metadata(metadata=metadata, image=image)
    assert isinstance(concatenated_data, bytes)

    metadata_length, unpacked_metadata, unpacked_image = unpack_vending_stream_data(
        concatenated_data
    )

    assert isinstance(metadata_length, int)
    assert unpacked_metadata == metadata

    unpacked_image = cv2.imdecode(unpacked_image, cv2.IMREAD_COLOR)
    assert isinstance(unpacked_image, np.ndarray)

    height, width, channels = unpacked_image.shape
    assert height == TEST_IMAGE_HEIGHT
    assert width == TEST_IMAGE_WIDTH
    assert channels == 3
    assert unpacked_image.dtype == np.uint8


def test_task_executor(dummy_executor: DummyExecutor) -> None:
    executor = TaskExecutor(executor=dummy_executor)
    string = ""

    def dummy_task_ok() -> str:
        return "One Punch Man."

    def dummy_task_error() -> None:
        raise RuntimeError

    def dummy_callback(future: Future) -> None:
        nonlocal string

        try:
            string = future.result()
        except Exception:
            string = "Exception occured."

    executor.add_task(task_fn=dummy_task_ok, done_callback=dummy_callback)
    assert string == "One Punch Man."

    executor.add_task(task_fn=dummy_task_error, done_callback=dummy_callback)
    assert string == "Exception occured."
