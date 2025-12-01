from typing import Generator

import pytest
from httpx import Response
from pytest import CaptureFixture
from respx import Route

from arseille.enums import Weather
from arseille.services import get_current_weather


@pytest.fixture
def clear_cache() -> Generator[None, None, None]:
    yield
    get_current_weather.cache_clear()


@pytest.fixture(scope="module", autouse=True)
def clear_cache_after_tests() -> Generator[None, None, None]:
    yield
    get_current_weather.cache_clear()


@pytest.mark.parametrize(
    ["temperature", "expected_weather"],
    [
        (-5.1, Weather.COLD),
        (19.9, Weather.COLD),
        (20.0, Weather.MODERATE),
        (25.7, Weather.MODERATE),
        (30.0, Weather.MODERATE),
        (30.1, Weather.HOT),
        (38.6, Weather.HOT),
    ],
)
def test_get_current_weather_success(
    mocked_api: Route, temperature: float, expected_weather: Weather, clear_cache: None
) -> None:
    mocked_api.return_value = Response(
        status_code=200, json={"current": {"temp_c": temperature}}
    )

    weather = get_current_weather()

    assert weather == expected_weather


@pytest.mark.parametrize("error_code", [400, 401, 403, 500, 502, 503, 504])
def test_get_current_weather_failure(
    mocked_api: Route, error_code: int, capsys: CaptureFixture, clear_cache: None
) -> None:
    mocked_api.return_value = Response(
        status_code=error_code,
        json={"error": {"code": 1006, "message": "No matching location found."}},
    )

    weather = get_current_weather()

    captured = capsys.readouterr()

    assert weather == Weather.MODERATE
    assert (
        "Cannot get weather data. Now using default temperature value.\n"
        == captured.out
    )


@pytest.mark.parametrize("temperature", [15.5, 25.5, 35.5])
def test_get_current_weather_cache(mocked_api: Route, temperature: float) -> None:
    """
    Cache check. It should always return the result of the first parametrized value.
    """
    mocked_api.return_value = Response(
        status_code=200, json={"current": {"temp_c": temperature}}
    )

    weather = get_current_weather()

    assert weather == Weather.COLD
