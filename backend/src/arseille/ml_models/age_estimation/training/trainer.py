from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn, optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from arseille.ml_models.age_estimation.agenet import AgeEstimationModel, AgeRangeModel


def evaluate(
    age_range_model: nn.Module,
    age_estimation_model: nn.Module,
    validation_dataloader: DataLoader,
    device: torch.device,
    verbose: int = 0,
) -> tuple[float, float, float]:
    # Loss function
    age_range_loss = nn.CrossEntropyLoss()
    age_estimation_loss = nn.L1Loss()

    age_range_model = age_range_model.to(device)
    age_estimation_model = age_estimation_model.to(device)

    with torch.no_grad():
        age_range_model.eval()
        age_estimation_model.eval()

        age_range_accuracy = 0

        total_age_range_loss = 0
        total_age_estimation_loss = 0

        if verbose == 1:
            validation_dataloader = tqdm(  # ty: ignore[invalid-assignment], tqdm
                validation_dataloader, desc="Evaluate: ", ncols=100
            )

        for images, age_labels, actual_ages in validation_dataloader:
            batch_size = images.shape[0]

            images, age_labels, actual_ages = (
                images.to(device),
                age_labels.to(device),
                actual_ages.to(device),
            )

            prediction_age_labels = age_range_model(images)

            age_range_loss = age_range_loss(prediction_age_labels, age_labels.long())
            total_age_range_loss += age_range_loss.item()

            age_range_accuracy += (
                torch.sum(torch.argmax(prediction_age_labels, dim=1) == age_labels)
                / batch_size
            )

            estimated_ages = age_estimation_model(images, age_labels).view(-1)
            age_estimation_loss = age_estimation_loss(actual_ages, estimated_ages)

            total_age_estimation_loss += age_estimation_loss.item()

        validation_age_range_loss = total_age_range_loss / len(validation_dataloader)
        validation_age_range_accuracy = age_range_accuracy / len(validation_dataloader)

        validation_age_estimation_loss = total_age_estimation_loss / len(
            validation_dataloader
        )

        return (
            validation_age_range_loss,
            validation_age_range_accuracy,
            validation_age_estimation_loss,
        )


def train_model(
    epochs: int,
    steps_per_epoch: int,
    weights_path: str | Path,
    training_data: DataLoader,
    validation_data: DataLoader | None = None,
) -> None:
    """Train the model."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    training_data_iterator = iter(training_data)

    # Add model to device
    age_range_model = AgeRangeModel().to(device)
    age_estimation_model = AgeEstimationModel().to(device)

    # Loss function
    age_range_loss_fn = nn.CrossEntropyLoss()
    age_estimation_loss_fn = nn.L1Loss()

    # Optimizer
    age_range_optimizer = optim.Adam(age_range_model.parameters(), lr=5e-3)
    age_estimation_optimizer = optim.Adam(age_estimation_model.parameters(), lr=1e-3)

    # Scheduler
    age_range_scheduler = ReduceLROnPlateau(
        optimizer=age_range_optimizer, mode="min", factor=0.1, patience=3
    )
    age_estimation_scheduler = ReduceLROnPlateau(
        optimizer=age_estimation_optimizer, mode="min", factor=0.1, patience=3
    )

    # History
    history = {
        "train_age_range_loss": [],
        "train_age_range_accuracy": [],
        "validation_age_range_loss": [],
        "validation_age_range_accuracy": [],
    }

    count_steps = 1

    for epoch in range(1, epochs + 1):
        total_age_range_loss = 0
        age_range_accuracy = 0

        total_age_estimation_loss = 0

        age_range_model.train()
        age_estimation_model.train()

        for _ in tqdm(
            range(steps_per_epoch),
            desc=f"Epoch {epoch}/{epochs}: ",
            ncols=100,
        ):
            images, age_labels, actual_ages = next(training_data_iterator)
            batch_size = images.shape[0]

            images, age_labels, actual_ages = (
                images.to(device),
                age_labels.to(device),
                actual_ages.to(device),
            )

            prediction_age_labels = age_range_model(images)

            age_range_loss = age_range_loss_fn(prediction_age_labels, age_labels.long())
            total_age_range_loss += age_range_loss.item()

            age_range_accuracy += (
                torch.sum(torch.argmax(prediction_age_labels, dim=1) == age_labels)
                / batch_size
            )

            age_range_optimizer.zero_grad()
            age_range_loss.backward()
            age_range_optimizer.step()

            # Age estimation loss
            estimated_ages = age_estimation_model(images, age_labels).view(-1)
            age_estimation_loss = age_estimation_loss_fn(actual_ages, estimated_ages)

            age_estimation_optimizer.zero_grad()
            age_estimation_loss.backward()
            age_estimation_optimizer.step()

            total_age_estimation_loss += age_estimation_loss.item()

            if count_steps == len(training_data):
                training_data_iterator = iter(training_data)
                count_steps = 0

            count_steps += 1

        train_age_range_loss = total_age_range_loss / steps_per_epoch
        train_age_range_accuracy = age_range_accuracy / steps_per_epoch

        train_age_estimation_loss = total_age_estimation_loss / steps_per_epoch

        history["train_age_range_loss"].append(float(train_age_range_loss))
        history["train_age_range_accuracy"].append(float(train_age_range_accuracy))

        print(f"Training age range loss: {train_age_range_loss:.2f}")
        print(f"Training age range accuracy: {train_age_range_accuracy:.2f}")
        print(f"Training age estimation loss: {train_age_estimation_loss:.2f}")

        if validation_data:
            (
                validation_age_range_loss,
                validation_age_range_accuracy,
                validation_age_estimation_loss,
            ) = evaluate(
                age_range_model=age_range_model,
                age_estimation_model=age_estimation_model,
                validation_dataloader=validation_data,
                device=device,
            )

            history["validation_age_range_loss"].append(
                float(validation_age_range_loss)
            )
            history["validation_age_range_accuracy"].append(
                float(validation_age_range_accuracy)
            )

            age_range_scheduler.step(np.round(validation_age_range_loss, 3))
            age_estimation_scheduler.step(np.round(validation_age_estimation_loss, 3))

            print(f"Validation age range loss: {validation_age_range_loss:.2f}")
            print(f"Validation age range accuracy: {validation_age_range_accuracy:.2f}")
            print(
                f"Validation age estimation loss: {validation_age_estimation_loss:.2f}"
            )

    if weights_path:

        class dummy_model(nn.Module):
            def __init__(self) -> None:
                super().__init__()

                self.age_range_model = age_range_model
                self.age_estimation_model = age_estimation_model

            def forward(self, _: Any) -> None:
                return

        model = dummy_model()
        torch.save(model.state_dict(), weights_path)
