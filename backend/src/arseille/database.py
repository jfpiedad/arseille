from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from arseille.config import settings


async def initialize_db() -> AsyncMongoClient:
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

    return client
