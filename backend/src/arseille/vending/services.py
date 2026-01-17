from datetime import timedelta
from typing import Any

from bson import ObjectId
from cachetools.func import ttl_cache
from httpx import Client, HTTPError
from pymongo.asynchronous.database import AsyncDatabase

from arseille.config import settings
from arseille.vending.enums import Weather
from arseille.vending.schemas import TransactionCreate

client = Client()


@ttl_cache(maxsize=128, ttl=timedelta(minutes=15).seconds)
def get_current_weather() -> Weather:
    url = settings.WEATHER_API_BASE_URL

    query_params = {
        "q": settings.TARGET_CITY,
        "key": settings.WEATHER_API_KEY,
    }

    # Use this temperature value incase the API fails.
    temperature = 25

    try:
        response = client.get(url=f"{url}/current.json", params=query_params)

        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            temperature = data["current"]["temp_c"]
    except HTTPError:
        print("Cannot get weather data. Now using default temperature value.")

    if temperature < 20:
        weather = Weather.COLD
    elif 20 <= temperature <= 30:
        weather = Weather.MODERATE
    else:
        weather = Weather.HOT

    return weather


async def create_transaction_in_db(
    db: AsyncDatabase, transaction_data: TransactionCreate
) -> None:
    await db[settings.COLLECTION_NAME].insert_one(transaction_data.model_dump())


async def get_transaction_in_db(db: AsyncDatabase, id: str) -> dict[str, Any]:
    return await db[settings.COLLECTION_NAME].find_one({"_id": ObjectId(id)})  # ty: ignore[invalid-return-type]


async def get_all_transactions_in_db(db: AsyncDatabase) -> list[dict[str, Any]]:
    return await db[settings.COLLECTION_NAME].find({}).to_list()
