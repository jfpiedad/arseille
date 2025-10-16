from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_CONNECTION_STRING: str
    DB_NAME: str

    WEATHER_API_KEY: str
    WEATHER_API_BASE_URL: HttpUrl


settings = Settings()
