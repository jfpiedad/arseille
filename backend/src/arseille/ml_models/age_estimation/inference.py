import math
from pathlib import Path

import numpy as np
import torch
from mediapipe.tasks.python.components.containers.bounding_box import BoundingBox
from PIL import Image
from torchvision import transforms as T

from arseille.ml_models.age_estimation.agenet import Model


class AgeEstimator:
    def __init__(
        self,
        weights_path: str | Path,
        face_size: int = 64,
        thickness_per_pixel: int = 500,
    ) -> None:
        weights_path = Path(weights_path)

        if not weights_path.exists():
            raise FileNotFoundError(f"Path {weights_path} does not exist.")

        self.weights_path = weights_path
        self.face_size = face_size
        self.thickness_per_pixel = thickness_per_pixel

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model = Model().to(device=device)
        self.model.eval()

        self.model.load_state_dict(
            torch.load(self.weights_path, map_location="cpu"), strict=False
        )

    def predict_single(
        self, bounding_box: BoundingBox, image: np.ndarray
    ) -> int | float:
        """
        Predicts age on single image given the bounding box. \n
        **For testing purposes only.**
        """

        x1 = bounding_box.origin_x
        y1 = bounding_box.origin_y
        x2 = bounding_box.origin_x + bounding_box.width
        y2 = bounding_box.origin_y + bounding_box.height

        pil_image = Image.fromarray(image)

        box = [x1, y1, x2, y2]
        box = np.clip(box, 0, np.inf).astype(np.uint32)

        padding = max(image.shape) * 5 / self.thickness_per_pixel
        padding = int(max(padding, 10))

        box = self._padding_face(box=box)  # ty: ignore[invalid-argument-type]
        face = pil_image.crop(box)  # ty: ignore[invalid-argument-type]
        transformed_face = self._transform(face)

        face_image = torch.unsqueeze(transformed_face, dim=0)

        ages = self.model(face_image)
        ages = torch.round(ages).long()

        return ages[0].item()

    def predict(self, face_detection_data: list[tuple[BoundingBox, np.ndarray]]) -> int:
        """Predicts age based on face detection data."""

        images = []

        for bounding_box, image in face_detection_data:
            x1 = bounding_box.origin_x
            y1 = bounding_box.origin_y
            x2 = bounding_box.origin_x + bounding_box.width
            y2 = bounding_box.origin_y + bounding_box.height

            bounding_box = [x1, y1, x2, y2]
            bounding_box = np.clip(bounding_box, 0, np.inf).astype(np.uint32)

            image = Image.fromarray(image).crop(bounding_box)  # ty: ignore[invalid-argument-type]
            image = self._transform(image=image)

            images.append(image)

        cropped_images = torch.stack(images, dim=0)

        ages = self.model(cropped_images)
        ages = torch.round(ages).long()

        ages = [age[0].item() for age in ages]

        final_age = self._trimmed_ages_mean(ages=ages)

        return final_age

    def _transform(self, image: Image.Image) -> torch.Tensor:
        """Transform input face image for the model."""

        return T.Compose(
            [
                T.Resize((self.face_size, self.face_size)),
                T.ToTensor(),
                T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )(image)

    def _padding_face(self, box: list[int], padding: int = 10) -> list[int]:
        """Add padding to the bounding box."""
        return [box[0] - padding, box[1] - padding, box[2] + padding, box[3] + padding]

    def _trimmed_ages_mean(self, ages: list[int], trim_ratio: float = 0.2) -> int:
        """
        Trims the list of ages with the given ratio to filter out noise/false positives
        and return the mean of the trimmed list as the final age value.
        """

        ages.sort()
        length = len(ages)

        trim_length = math.floor(length * trim_ratio)

        if 2 * trim_length >= length:
            raise ValueError(f"Trim ratio too large for a list of length {length}")

        trimmed_ages = ages[trim_length : length - trim_length]

        age = round(np.mean(trimmed_ages))

        return age
