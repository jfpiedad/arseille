from typing import Callable

import mediapipe
from mediapipe.tasks.python.components.containers.detections import DetectionResult
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)
from mediapipe.tasks.python.vision.face_detector import (
    FaceDetector,
    FaceDetectorOptions,
)

from arseille.config import settings


def initialize_face_detector(
    callback: Callable[[DetectionResult, mediapipe.Image, int], None],
) -> FaceDetector:
    """Initialize face detector object from Mediapipe."""
    model_asset_path = settings.ROOT_DIRECTORY / "weights" / "blazeface.tflite"

    if not model_asset_path.exists():
        raise FileNotFoundError(f"Path {model_asset_path} does not exist.")

    base_options = BaseOptions(model_asset_path=model_asset_path)
    options = FaceDetectorOptions(
        base_options=base_options,
        running_mode=VisionTaskRunningMode.LIVE_STREAM,
        result_callback=callback,
    )

    return FaceDetector.create_from_options(options=options)
