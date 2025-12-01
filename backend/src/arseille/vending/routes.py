from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from arseille.vending.dependencies import get_vending_machine
from arseille.vending.utils import concatenate_image_and_metadata
from arseille.vending.vending_machine import VendingMachine

router = APIRouter()


@router.websocket("/vending-machine/stream")
async def vending_machine_checkpoint(
    websocket: WebSocket,
    vending: Annotated[VendingMachine, Depends(get_vending_machine)],
) -> None:
    await websocket.accept()
    await vending.set_unavailable()

    try:
        async for image, timestamp_ms in vending.video_source.read():
            vending.face_detector.detect_async(image=image, timestamp_ms=timestamp_ms)

            if vending.metadata_obj.annotated_image is not None:
                message = concatenate_image_and_metadata(
                    metadata=vending.metadata_obj.to_dict(),
                    image=vending.metadata_obj.annotated_image,
                )
                await websocket.send_bytes(data=message)
    except WebSocketDisconnect:
        print("Websocket connection was disconnected.")
    except Exception as exc:
        print(f"Websocket connection was closed abruptly. \n {exc}")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="An unexpected error occured.",
        )
    finally:
        vending.clear_metadata_obj()
        vending.clear_recent_detection_results()
        vending.set_available()
