from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status
from pymongo.asynchronous.database import AsyncDatabase

from arseille.vending.dependencies import get_db, get_vending_machine
from arseille.vending.enums import VendingMode
from arseille.vending.schemas import Transaction
from arseille.vending.services import (
    get_all_transactions_in_db,
)
from arseille.vending.utils import concatenate_image_and_metadata
from arseille.vending.vending_machine import VendingMachine

router = APIRouter(prefix="/vending-machine")


@asynccontextmanager
async def ws_exception_handler(
    websocket: WebSocket, run_type: str
) -> AsyncGenerator[None, None]:
    """
    Context manager to handle WebSocket lifecycle exceptions.
    """

    await websocket.accept()

    try:
        yield
    except WebSocketDisconnect:
        print(f"Websocket ({run_type}) disconnected by client.")
    except Exception:
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Internal Server Error",
            )
        except RuntimeError:
            # Socket may already be closed.
            pass

        raise


@router.websocket("/checkpoint")
async def vending_machine_checkpoint(
    websocket: WebSocket,
    vending_machine: Annotated[VendingMachine, Depends(get_vending_machine)],
) -> None:
    async with ws_exception_handler(websocket=websocket, run_type="Checkpoint"):
        async with vending_machine as vm:
            async for metadata in vm.run_checkpoint():
                if metadata.annotated_image is not None:
                    message = concatenate_image_and_metadata(
                        metadata=metadata.to_dict(),
                        image=metadata.annotated_image,
                    )
                    await websocket.send_bytes(data=message)


@router.websocket("/full-system")
async def vending_machine(
    websocket: WebSocket,
    vending_machine: Annotated[VendingMachine, Depends(get_vending_machine)],
    db: Annotated[AsyncDatabase, Depends(get_db)],
) -> None:
    async with ws_exception_handler(websocket=websocket, run_type="Simulation"):
        async with vending_machine as vm:
            await vm.simulate(websocket=websocket, db=db)


@router.websocket("/camera-stream")
async def vending_machine_camera_stream(websocket: WebSocket) -> None:
    vm: VendingMachine = websocket.state.vending_machine
    vm.set_mode(VendingMode.FULL_SYSTEM)

    async with ws_exception_handler(websocket=websocket, run_type="Camera Stream"):
        async for image in vm.run():
            if image is not None:
                await websocket.send_bytes(data=image)


@router.get("/transactions", response_model=list[Transaction])
async def get_transactions(request: Request) -> Any:
    return await get_all_transactions_in_db(db=request.state.database)
