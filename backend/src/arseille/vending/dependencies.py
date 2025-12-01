from fastapi import WebSocket, WebSocketException, status

from arseille.vending.enums import VendingMode
from arseille.vending.vending_machine import VendingMachine


async def get_vending_machine(websocket: WebSocket, mode: int) -> VendingMachine:
    vending = websocket.state.vending_machine

    mode_mapping = {
        1: VendingMode.CHECKPOINT_25,
        2: VendingMode.CHECKPOINT_50,
        3: VendingMode.CHECKPOINT_75,
    }

    if mode not in mode_mapping:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    vending.set_mode(mode=mode_mapping[mode])

    return vending
