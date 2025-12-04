from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from arseille.vending.dependencies import get_vending_machine
from arseille.vending.utils import concatenate_image_and_metadata
from arseille.vending.vending_machine import VendingMachine

router = APIRouter()


@router.websocket("/vending-machine/checkpoint")
async def vending_machine_checkpoint(
    websocket: WebSocket,
    vending_machine: Annotated[VendingMachine, Depends(get_vending_machine)],
) -> None:
    await websocket.accept()

    async with vending_machine as vm:
        try:
            async for metadata in vm.run_checkpoint():
                if metadata.annotated_image is not None:
                    message = concatenate_image_and_metadata(
                        metadata=metadata.to_dict(),
                        image=metadata.annotated_image,
                    )
                    await websocket.send_bytes(data=message)
        except WebSocketDisconnect:
            print("Websocket disconnected by client.")
        except Exception as exc:
            print(f"Unexpected error in vending checkpoint. \n {exc}")
            try:
                await websocket.close(
                    code=status.WS_1011_INTERNAL_ERROR,
                    reason="Internal Server Error",
                )
            except RuntimeError:
                # Socket may already be closed.
                pass
