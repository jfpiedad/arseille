from pathlib import Path

from pydantic import HttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_CONNECTION_STRING: str
    DB_NAME: str

    TARGET_CITY: str
    WEATHER_API_KEY: str
    WEATHER_API_BASE_URL: HttpUrl

    @computed_field
    @property
    def ROOT_DIRECTORY(self) -> Path:
        return Path(__file__).resolve().parents[3]


settings = Settings()
