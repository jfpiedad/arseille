from datetime import timedelta

import httpx
from cachetools.func import ttl_cache
from httpx import HTTPError

from arseille.config import settings
from arseille.enums import Weather


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
        response = httpx.get(url=f"{url}/current.json", params=query_params)
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
