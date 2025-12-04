import os
from typing import AsyncGenerator, Generator

import pytest
import respx
from fastapi import WebSocket, WebSocketException, status
from httpx import AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport
from respx import Route

from arseille.config import settings
from arseille.main import app
from arseille.vending.dependencies import get_vending_machine
from arseille.vending.enums import VendingMode
from arseille.vending.utils import TaskExecutor
from arseille.vending.vending_machine import VendingMachine
from tests.utils import (
    DummyAgeEstimator,
    DummyExecutor,
    DummyFaceDetector,
    DummyVideoSource,
    create_dummy_vending_machine,
)

if os.getenv("APP_ENV") != "test":
    raise RuntimeError("Not in a test environment.")


async def override_get_vending_machine(
    websocket: WebSocket, mode: int
) -> VendingMachine:
    mode_mapping = {
        1: VendingMode.CHECKPOINT_25,
        2: VendingMode.CHECKPOINT_50,
        3: VendingMode.CHECKPOINT_75,
    }

    if mode not in mode_mapping:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    vm = create_dummy_vending_machine()

    vm.set_mode(mode=mode_mapping[mode])

    return vm


app.dependency_overrides[get_vending_machine] = override_get_vending_machine


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGIWebSocketTransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="module")
def mocked_api() -> Generator[Route, None, None]:
    query_params = {"q": settings.TARGET_CITY, "key": settings.WEATHER_API_KEY}

    with respx.mock(
        base_url=str(settings.WEATHER_API_BASE_URL), assert_all_called=False
    ) as respx_mock:
        weather_api = respx_mock.get("/current.json", params=query_params)

        yield weather_api


@pytest.fixture(scope="module")
def dummy_executor() -> Generator[DummyExecutor, None, None]:
    executor = DummyExecutor()
    yield executor
    executor.shutdown(wait=True)


@pytest.fixture(scope="module")
def dummy_vending_machine(
    dummy_executor: DummyExecutor,
) -> Generator[VendingMachine, None, None]:
    vm = VendingMachine(
        video_source=DummyVideoSource(),
        face_detector=None,
        age_estimator=DummyAgeEstimator(),
        task_executor=TaskExecutor(executor=dummy_executor),
    )

    face_detector = DummyFaceDetector()
    face_detector.callback = vm._result_callback
    vm.face_detector = face_detector

    yield vm

    vm.cleanup()


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"
