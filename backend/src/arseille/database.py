from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from arseille.config import settings


@asynccontextmanager
async def initialize_db(app: FastAPI) -> Any:
    client = AsyncMongoClient(
        host=settings.DB_CONNECTION_STRING,
        server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
    )

    try:
        await client.admin.command("ping")
        print("Successfully connected to the database.")
    except Exception as exc:
        raise Exception(
            f"Cannot connect to the database.\nThe following error occured: {exc}"
        )

    database = client[settings.DB_NAME]

    yield {"db": database}

    await client.close()
