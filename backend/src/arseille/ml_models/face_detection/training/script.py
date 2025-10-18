from pathlib import Path

import torch
from torch import optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from typer import Typer

from arseille.ml_models.face_detection.blazeface import BlazeFace
from arseille.ml_models.face_detection.training.data_loader import get_dataloader
from arseille.ml_models.face_detection.training.trainer import train_model
from arseille.ml_models.face_detection.utils import MultiBoxLoss

cli = Typer(name="Train face detection model", pretty_exceptions_enable=False)


@cli.command()
def training(
    batch_size: int = 256,
    image_size: int = 128,
    epochs: int = 10,
    dataset_directory: Path | None = None,
    learning_rate: float = 0.001,
    patience: float = 10,
    weights_path: Path | None = None,
    shuffle: bool = True,
    test: bool = False,
) -> None:
    """Train face detection model."""

    root_directory = Path(__file__).resolve().parents[6]

    if dataset_directory is None:
        dataset_directory = (
            root_directory / "datasets" / "face_detection" / "OpenImagesV7"
        )

    if test:
        batch_size = 1
        epochs = 1

    training_data = get_dataloader(
        directory=dataset_directory,
        image_size=image_size,
        batch_size=batch_size,
        shuffle=shuffle,
    )

    validation_data = get_dataloader(
        directory=dataset_directory,
        image_size=image_size,
        batch_size=batch_size,
        shuffle=shuffle,
        is_training=False,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if image_size == 256:
        face_detection_model = BlazeFace(use_back_model=True)
    else:
        face_detection_model = BlazeFace()

    face_detection_model = face_detection_model.to(device)

    if weights_path is None:
        weights_path = root_directory / "weights" / "blazeface.pt"

    anchors_path = root_directory / "anchors.npy"

    if not anchors_path.exists():
        raise Exception("Anchors file does not exist.")

    face_detection_model.load_anchors(str(anchors_path))

    criterion = MultiBoxLoss(
        jaccard_thresh=0.5,
        negpos_ratio=3,
        device=device,
        dbox_list=face_detection_model.dbox_list,
    )

    optimizer = optim.Adam(face_detection_model.parameters(), lr=learning_rate)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=patience)

    train_model(
        epochs=epochs,
        face_detection_model=face_detection_model,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        training_data=training_data,
        validation_data=validation_data,
        device=device,
        weights_path=weights_path,
    )


if __name__ == "__main__":
    cli()
