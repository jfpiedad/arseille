import asyncio

from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketException
from pymongo.asynchronous.database import AsyncDatabase

from arseille.vending.enums import VendingMode
from arseille.vending.vending_machine import VendingMachine


async def get_vending_machine(
    websocket: WebSocket, mode: int | None = None
) -> VendingMachine:
    vending: VendingMachine = websocket.state.vending_machine

    try:
        await asyncio.wait_for(vending._lock.acquire(), timeout=3.0)
        vending._lock.release()
    except asyncio.TimeoutError:
        raise WebSocketException(code=status.WS_1013_TRY_AGAIN_LATER)

    mode_mapping = {
        1: VendingMode.CHECKPOINT_25,
        2: VendingMode.CHECKPOINT_50,
        3: VendingMode.CHECKPOINT_75,
    }

    if mode is None:
        vending.set_mode(mode=VendingMode.FULL_SYSTEM)
    else:
        vending.set_mode(mode=mode_mapping[mode])

    return vending


async def get_db(websocket: WebSocket) -> AsyncDatabase:
    return websocket.state.database
