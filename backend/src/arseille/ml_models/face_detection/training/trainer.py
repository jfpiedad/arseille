from pathlib import Path

import torch
from torch import optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from arseille.ml_models.face_detection.blazeface import BlazeFace
from arseille.ml_models.face_detection.utils import MultiBoxLoss


def train_model(
    epochs: int,
    face_detection_model: BlazeFace,
    criterion: MultiBoxLoss,
    optimizer: optim.Adam,
    scheduler: ReduceLROnPlateau,
    training_data: DataLoader,
    validation_data: DataLoader,
    device: torch.device,
    weights_path: str | Path,
) -> None:
    """Train the model."""

    for epoch in range(epochs):
        # Train
        running_loss = 0.0
        running_localization_loss = 0.0
        running_class_loss = 0.0

        for images, targets in tqdm(training_data):
            images = images.to(device)
            targets = [annotation.to(device) for annotation in targets]

            optimizer.zero_grad()

            outputs = face_detection_model(images)

            localization_loss, confidence_loss = criterion(outputs, targets)
            total_loss = localization_loss + confidence_loss
            total_loss.backward()

            optimizer.step()

            running_loss += total_loss.item()
            running_localization_loss += localization_loss.item()
            running_class_loss += confidence_loss.item()

        # Eval
        face_detection_model.eval()

        validation_loss = 0.0
        validation_localization_loss = 0.0
        validation_class_loss = 0.0

        with torch.no_grad():
            for images, targets in validation_data:
                images = images.to(device)
                targets = [annotation.to(device) for annotation in targets]

                outputs = face_detection_model(images)

                localization_loss, confidence_loss = criterion(outputs, targets)
                total_loss = localization_loss + confidence_loss

                validation_loss += total_loss.item()
                validation_localization_loss += localization_loss.item()
                validation_class_loss += confidence_loss.item()

        training_data_length = len(training_data)
        validation_data_length = len(validation_data)

        training_loss = running_loss / training_data_length
        training_localization_loss = running_localization_loss / training_data_length
        training_class_loss = running_class_loss / training_data_length

        validation_loss = validation_loss / validation_data_length

        print(f"[{epoch + 1}]: ")

        print(f"Training loss: {training_loss:.3f}")
        print(f"Validation loss: {validation_loss:.3f}")
        print(f"Training localization loss: {training_localization_loss:.3f}")
        print(f"Training class loss: {training_class_loss:.3f}")

        scheduler.step(validation_loss)

        torch.save(face_detection_model.state_dict(), weights_path)


if __name__ == "__main__":
    pass
