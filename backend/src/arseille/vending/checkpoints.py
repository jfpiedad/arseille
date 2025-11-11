from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)

from arseille.vending.utils import concatenate_image_and_metadata
from arseille.vending.vending_machine import VendingMachine, VendingMode

router = APIRouter()


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


@router.websocket("/ws/checkpoint/{mode}")
async def checkpoint_25(
    websocket: WebSocket,
    vending: Annotated[VendingMachine, Depends(get_vending_machine)],
) -> None:
    await websocket.accept()
    await vending.set_unavailable()

    try:
        async for image, timestamp_ms in vending.read_frame_from_webcam():
            vending.face_detector.detect_async(image=image, timestamp_ms=timestamp_ms)

            if vending.annotated_image is not None:
                message = concatenate_image_and_metadata(
                    metadata=vending.detection_metadata, image=vending.annotated_image
                )
                await websocket.send_bytes(data=message)

    except WebSocketDisconnect:
        print("Websocket connection was disconnected.")
    except Exception:
        print("Websocket connection was closed abruptly.")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="An unexpected error occured."
        )
    finally:
        vending.set_available()
