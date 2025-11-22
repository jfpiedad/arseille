from pathlib import Path

from typer import Typer

from arseille.config import settings
from arseille.ml_models.age_estimation.training.data_loader import (
    get_dataloader,
    split_dataloader,
)
from arseille.ml_models.age_estimation.training.trainer import train_model

cli = Typer(name="Training age estimation model", pretty_exceptions_enable=False)


@cli.command()
def training(
    batch_size: int = 128,
    image_size: int = 64,
    epochs: int = 100,
    steps_per_epoch: int | None = None,
    training_data_directory: Path | None = None,
    validation_data_directory: Path | None = None,
    validation_ratio: float | None = None,
    weights_path: Path | None = None,
    shuffle: bool = True,
    num_workers: int = 1,
    test: bool = False,
) -> None:
    """Train age estimation model."""

    root_directory = settings.ROOT_DIRECTORY
    dataset_directory = root_directory / "datasets" / "age_estimation"

    if training_data_directory is None:
        training_data_directory = dataset_directory / "UTKFace"

    if test:
        batch_size = 1
        epochs = 1

    training_data = get_dataloader(
        directory=training_data_directory,
        image_size=image_size,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
    )

    if validation_data_directory is not None:
        validation_data = get_dataloader(
            directory=validation_data_directory,
            image_size=image_size,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
        )
    elif validation_ratio is not None:
        training_data, validation_data = split_dataloader(
            training_data=training_data, validation_ratio=validation_ratio
        )
    else:
        validation_data = None

    if steps_per_epoch is None:
        steps_per_epoch = len(training_data)

    if weights_path is None:
        weights_path = root_directory / "weights" / "agenet.pt"
        weights_path.parent.mkdir(parents=True, exist_ok=True)

    train_model(
        epochs=epochs,
        steps_per_epoch=steps_per_epoch,
        weights_path=weights_path,
        training_data=training_data,
        validation_data=validation_data,
    )


if __name__ == "__main__":
    cli()
