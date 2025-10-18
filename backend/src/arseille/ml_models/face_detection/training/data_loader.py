from pathlib import Path
from typing import Any

import albumentations as A
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms as T

from arseille.ml_models.face_detection.utils import od_collate_fn


class OpenImagesV7Dataset(Dataset):
    dataset_filenames: list[str]

    def __init__(
        self,
        directory: str | Path,
        image_size: int,
        transform: T.Compose | None = None,
        augment: A.Compose | None = None,
        is_training: bool = True,
    ) -> None:
        if isinstance(directory, str):
            self.directory = Path(directory)
        else:
            self.directory = directory

        if is_training:
            phase = "train"
        else:
            phase = "val"

        self.images_directory = self.directory / "images" / phase
        self.labels_directory = self.directory / "labels" / phase

        self.image_size = image_size
        self.transform = transform
        self.augment = augment
        self.dataset_filenames = self._get_filenames()

    def __len__(self) -> int:
        return len(self.dataset_filenames)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, np.ndarray]:
        image_path = self.images_directory / f"{self.dataset_filenames[index]}.jpg"
        image = self._load_image(image_path)

        rescale_output = self._resize_and_pad(image, target_size=self.image_size)
        image = rescale_output["image"]

        label_path = self.labels_directory / f"{self.dataset_filenames[index]}.txt"
        label = self._read_and_convert_labels(label_path, rescale_output=rescale_output)

        if self.augment is not None:
            augmented = self.augment(image=image, bboxes=label)
            image = augmented["image"]
            label = np.array(augmented["bboxes"])

        return self.transform(image.copy()), np.clip(label, 0, 1)

    def _get_filenames(self) -> list[Path]:
        filenames = []

        for file_path in self.labels_directory.iterdir():
            filenames.append(file_path.stem)

        return filenames

    @staticmethod
    def _load_image(image_path: str) -> np.ndarray:
        """Load an image from given image path."""

        image = plt.imread(image_path)

        if len(image.shape) == 2 or image.shape[2] == 1:
            image = np.stack((image,) * 3, axis=-1)

        if image.shape[2] == 4:
            image = image[:, :, :3]

        return image

    @staticmethod
    def _read_and_convert_labels(label_path: str, rescale_output: dict) -> np.ndarray:
        """Read and convert labels from YOLO format to x1, y1, x2, y2 format."""

        annotations = pd.read_csv(label_path, header=None, sep=" ")
        labels = annotations.values[:, 0]

        yolo_bounding_boxes = annotations.values[:, 1:]

        cx = yolo_bounding_boxes[:, 0]
        cy = yolo_bounding_boxes[:, 1]

        width = yolo_bounding_boxes[:, 2]
        height = yolo_bounding_boxes[:, 3]

        x1 = (cx - width / 2) * rescale_output["x_ratio"] + rescale_output["x_offset"]
        x2 = (cy + width / 2) * rescale_output["x_ratio"] + rescale_output["x_offset"]
        y1 = (cy - height / 2) * rescale_output["y_ratio"] + rescale_output["y_offset"]
        y2 = (cy + height / 2) * rescale_output["y_ratio"] + rescale_output["y_offset"]

        x1 = np.expand_dims(x1, 1)
        x2 = np.expand_dims(x2, 1)
        y1 = np.expand_dims(y1, 1)
        y2 = np.expand_dims(y2, 1)

        target = np.concatenate([x1, y1, x2, y2, labels.reshape(-1, 1)], axis=1).clip(
            0.0, 1.0
        )

        return target

    @staticmethod
    def _resize_and_pad(image: np.ndarray, target_size: int = 128) -> dict[str, Any]:
        """
        Resize image to square `target_size`, and pad if needed to avoid deformation.
        """

        if image.shape[0] > image.shape[1]:
            new_y = target_size
            new_x = int(target_size * image.shape[1] / image.shape[0])
        else:
            new_y = int(target_size * image.shape[0] / image.shape[1])
            new_x = target_size

        output_image = cv2.resize(image, (new_x, new_y))

        top = max(0, new_x - new_y) // 2
        bottom = target_size - new_y - top
        left = max(0, new_y - new_x) // 2
        right = target_size - new_x - left

        output_image = cv2.copyMakeBorder(
            output_image,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=(128, 128, 128),
        )

        x_ratio = new_x / target_size
        y_ratio = new_y / target_size
        x_offset = left / target_size
        y_offset = top / target_size

        return {
            "image": output_image,
            "x_ratio": x_ratio,
            "x_offset": x_offset,
            "y_ratio": y_ratio,
            "y_offset": y_offset,
        }


def get_dataloader(
    directory: str | Path,
    image_size: int,
    batch_size: int,
    shuffle: bool,
    is_training: bool = True,
) -> DataLoader:
    transform = T.Compose(
        [
            T.ToTensor(),
            T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            T.Resize((image_size, image_size)),
        ]
    )

    augment = None

    # Create augment if its training data
    if is_training:
        augment = A.Compose(
            [
                A.RandomBrightnessContrast(brightness_limit=0.2),
                A.HorizontalFlip(p=0.5),
                A.RandomCropFromBorders(
                    crop_left=0.05,
                    crop_right=0.05,
                    crop_top=0.05,
                    crop_bottom=0.05,
                    p=0.9,
                ),
                A.Affine(
                    rotate=(-30, 30),
                    scale=(0.8, 1.1),
                    keep_ratio=True,
                    translate_percent=(-0.05, 0.05),
                    p=0.9,
                ),
            ],
            bbox_params=A.BboxParams(format="albumentations"),
        )

    dataset = OpenImagesV7Dataset(
        directory=directory,
        image_size=image_size,
        transform=transform,
        augment=augment,
        is_training=is_training,
    )

    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=od_collate_fn,
    )
