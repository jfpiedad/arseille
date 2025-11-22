from pathlib import Path

from PIL import Image
from PIL.ImageFile import ImageFile
from torch.utils.data import DataLoader, Dataset, SubsetRandomSampler
from torchvision import transforms as T
from torchvision.transforms import Compose


class UTKFaceDataset(Dataset):
    """
    Labels for each face image are embedded in the file name.

    The format is: `[age]_[gender]_[race]_[date&time]`.
    """

    dataset_filenames: list[str]

    def __init__(self, directory: str | Path, transform: Compose | None = None) -> None:
        self.directory = Path(directory)
        self.transform = transform
        self.dataset_filenames = self._get_filenames()

    def __len__(self) -> int:
        return len(self.dataset_filenames)

    def __getitem__(self, index: int) -> tuple[ImageFile, int, int]:
        filename = self.dataset_filenames[index]

        image_labels = filename.split("_")

        actual_age = int(image_labels[0])
        age_label = self._age_to_class(actual_age)

        image_path = self.directory / filename

        with Image.open(image_path) as image:
            image = image.convert("RGB")
            if self.transform:
                image = self.transform(image)

        return image, age_label, actual_age

    def _get_filenames(self) -> list[Path]:
        filenames = []

        for file_path in self.directory.iterdir():
            if file_path.suffix in [".jpg", ".jpeg", ".png"]:
                filename = file_path.name
                labels = file_path.stem.split("_")

                if len(labels) == 4:
                    filenames.append(filename)

        if len(filenames) == 0:
            raise Exception(f"There are no images in the directory {self.directory}")

        return filenames

    @staticmethod
    def _age_to_class(age: int) -> int:
        age_ranges = [0, 4, 9, 15, 25, 35, 45, 60, 75]

        if age > max(age_ranges):
            return len(age_ranges) - 1

        for index in range(len(age_ranges) - 1):
            if age_ranges[index] <= age <= age_ranges[index + 1]:
                return index


def get_dataloader(
    directory: str | Path,
    image_size: int,
    batch_size: int,
    shuffle: bool,
    num_workers: int,
) -> DataLoader:
    transform = T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.RandomHorizontalFlip(0.2),
            T.RandomRotation(10),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )

    dataset = UTKFaceDataset(directory=directory, transform=transform)

    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        drop_last=True,
    )


def split_dataloader(
    training_data: DataLoader, validation_ratio: float
) -> tuple[DataLoader, DataLoader]:
    """Split training data for validation data by the given ratio"""
    training_ratio = 1 - validation_ratio
    training_size = int(training_ratio * len(training_data.dataset))

    indices = list(range(len(training_data.dataset)))
    training_indices = indices[:training_size]
    validation_indices = indices[training_size:]

    dataset = training_data.dataset
    batch_size = training_data.batch_size
    num_workers = training_data.num_workers

    train_sampler = SubsetRandomSampler(training_indices)
    validation_sampler = SubsetRandomSampler(validation_indices)

    training_data = DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=num_workers,
        drop_last=True,
    )

    validation_data = DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        sampler=validation_sampler,
        num_workers=num_workers,
        drop_last=True,
    )

    return training_data, validation_data
