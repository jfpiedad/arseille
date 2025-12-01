import os
from pathlib import Path

from pydantic import HttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    environment = os.getenv("APP_ENV", default="dev")

    if environment == "test":
        return ".env.test"
    else:
        return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=get_env_file(), extra="ignore")

    DB_CONNECTION_STRING: str
    DB_NAME: str

    TARGET_CITY: str
    WEATHER_API_KEY: str
    WEATHER_API_BASE_URL: HttpUrl

    @computed_field
    @property
    def ROOT_DIRECTORY(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @computed_field
    @property
    def FACE_DETECTOR_WEIGHTS_PATH_TRAINING(self) -> Path:
        """Face detector weights path."""
        return self.ROOT_DIRECTORY / "weights" / "blazeface.pt"

    @computed_field
    @property
    def FACE_DETECTOR_WEIGHTS_PATH_INFERENCE(self) -> Path:
        """Face detector weights path."""
        return self.ROOT_DIRECTORY / "weights" / "blazeface.tflite"

    @computed_field
    @property
    def AGE_ESTIMATOR_WEIGHTS_PATH(self) -> Path:
        """Age estimator weights path."""
        return self.ROOT_DIRECTORY / "weights" / "agenet.pt"

    @computed_field
    @property
    def FACE_DETECTOR_DATASET_PATH(self) -> Path:
        """Face detector dataset path."""
        return self.ROOT_DIRECTORY / "datasets" / "face_detection"

    @computed_field
    @property
    def AGE_ESTIMATOR_DATASET_PATH(self) -> Path:
        """Age estimator dataset path."""
        return self.ROOT_DIRECTORY / "datasets" / "age_estimation"


settings = Settings()
