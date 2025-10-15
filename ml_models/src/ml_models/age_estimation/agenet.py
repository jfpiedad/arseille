import torch
from torch import nn


class AgeRangeModel(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 9,
    ) -> None:
        super().__init__()

        self.Conv1 = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, 1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.Conv2 = nn.Sequential(
            nn.Conv2d(64, 256, 3, 1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.Conv3 = nn.Sequential(
            nn.Conv2d(256, 512, 3, 1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.adap = nn.AdaptiveAvgPool2d((2, 2))

        self.out_age = nn.Sequential(nn.Linear(2048, num_classes))

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        batch_size = input_tensor.shape[0]
        input_tensor = self.Conv1(input_tensor)
        input_tensor = self.Conv2(input_tensor)
        input_tensor = self.Conv3(input_tensor)

        input_tensor = self.adap(input_tensor)

        input_tensor = input_tensor.view(batch_size, -1)

        input_tensor = self.out_age(input_tensor)

        return input_tensor


class AgeEstimationModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding_layer = nn.Embedding(9, 64)

        self.Conv1 = nn.Sequential(
            nn.Conv2d(3, 64, 3, 1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.Conv2 = nn.Sequential(
            nn.Conv2d(64, 256, 3, 1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.Conv3 = nn.Sequential(
            nn.Conv2d(256, 512, 3, 1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Dropout2d(0.3),
            nn.MaxPool2d(2),
        )

        self.adap = nn.AdaptiveAvgPool2d((2, 2))

        self.out_age = nn.Sequential(nn.Linear(2048 + 64, 1), nn.ReLU())

    def forward(
        self, image_tensor: torch.Tensor, metadata_tensor: torch.Tensor
    ) -> torch.Tensor:
        batch_size = image_tensor.shape[0]
        image_tensor = self.Conv1(image_tensor)
        image_tensor = self.Conv2(image_tensor)
        image_tensor = self.Conv3(image_tensor)

        image_tensor = self.adap(image_tensor)

        image_tensor = image_tensor.view(batch_size, -1)

        metadata_tensor = self.embedding_layer(metadata_tensor)

        combined_tensor = torch.cat([image_tensor, metadata_tensor], dim=1)

        output = self.out_age(combined_tensor)

        return output


class Model(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.age_range_model = AgeRangeModel()
        self.age_estimation_model = AgeEstimationModel()

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        if len(input_tensor.shape) == 3:
            input_tensor = input_tensor[None, ...]

        age_ranges = self.age_range_model(input_tensor)

        predicted_age_range_indices = torch.argmax(age_ranges, dim=1).view(-1)

        estimated_ages = self.age_estimation_model(
            input_tensor, predicted_age_range_indices
        )

        return estimated_ages
