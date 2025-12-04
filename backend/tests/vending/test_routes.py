import json
from typing import AsyncGenerator

import cv2
import numpy as np
import pytest
from httpx import AsyncClient, Response
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from pytest import FixtureRequest
from respx import Route

from arseille.vending.enums import Weather
from tests.utils import DummyFaceDetector, unpack_vending_stream_data
from tests.vending.test_utils import TEST_IMAGE_HEIGHT, TEST_IMAGE_WIDTH

TEST_VENDING_MACHINE_STREAM_URL = "http://test/vending-machine/checkpoint"


@pytest.fixture
async def ws_client(
    client: AsyncClient, request: FixtureRequest
) -> AsyncGenerator[AsyncWebSocketSession, None]:
    async with aconnect_ws(
        url=f"{TEST_VENDING_MACHINE_STREAM_URL}?mode={request.param}",
        client=client,
    ) as ws:
        yield ws
        DummyFaceDetector._RAISE_WEBSOCKET_DISCONNECT = True


@pytest.mark.parametrize("ws_client", [1], indirect=True)
@pytest.mark.anyio
async def test_vending_machine_checkpoint_25(
    ws_client: AsyncWebSocketSession, mocked_api: Route
) -> None:
    mocked_api.return_value = Response(
        status_code=200, json={"current": {"temp_c": 32.5}}
    )

    for _ in range(20):
        data = await ws_client.receive_bytes(timeout=3.0)

        metadata_length, metadata, image = unpack_vending_stream_data(data)

        assert metadata_length == len(json.dumps(metadata))

        assert isinstance(metadata, dict)
        assert metadata["age"] is None
        assert metadata["weather"] is None
        assert isinstance(metadata["timestamp"], int)

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        assert isinstance(image, np.ndarray)

        height, width, channels = image.shape
        assert height == TEST_IMAGE_HEIGHT
        assert width == TEST_IMAGE_WIDTH
        assert channels == 3
        assert image.dtype == np.uint8


@pytest.mark.parametrize("ws_client", [2], indirect=True)
@pytest.mark.anyio
async def test_vending_machine_checkpoint_50(
    ws_client: AsyncWebSocketSession, mocked_api: Route
) -> None:
    mocked_api.return_value = Response(
        status_code=200, json={"current": {"temp_c": 32.5}}
    )

    age = None

    for index in range(60):
        if index == 20:
            age = 25

        data = await ws_client.receive_bytes(timeout=3.0)

        metadata_length, metadata, image = unpack_vending_stream_data(data)

        assert metadata_length == len(json.dumps(metadata))

        assert isinstance(metadata, dict)
        assert metadata["age"] == age
        assert metadata["weather"] is None
        assert isinstance(metadata["timestamp"], int)

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        assert isinstance(image, np.ndarray)

        height, width, channels = image.shape
        assert height == TEST_IMAGE_HEIGHT
        assert width == TEST_IMAGE_WIDTH
        assert channels == 3
        assert image.dtype == np.uint8


@pytest.mark.parametrize("ws_client", [3], indirect=True)
@pytest.mark.anyio
async def test_vending_machine_checkpoint_75(
    ws_client: AsyncWebSocketSession, mocked_api: Route
) -> None:
    mocked_api.return_value = Response(
        status_code=200, json={"current": {"temp_c": 32.5}}
    )

    age = None
    weather = None

    for index in range(60):
        if index == 20:
            age = 25
            weather = Weather.HOT

        data = await ws_client.receive_bytes(timeout=3.0)

        metadata_length, metadata, image = unpack_vending_stream_data(data)

        assert metadata_length == len(json.dumps(metadata))

        assert isinstance(metadata, dict)
        assert metadata["age"] == age
        assert metadata["weather"] == weather
        assert isinstance(metadata["timestamp"], int)

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        assert isinstance(image, np.ndarray)

        height, width, channels = image.shape
        assert height == TEST_IMAGE_HEIGHT
        assert width == TEST_IMAGE_WIDTH
        assert channels == 3
        assert image.dtype == np.uint8
