from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypedDict

from fastapi import FastAPI
from pymongo.asynchronous.database import AsyncDatabase

from arseille.config import settings
from arseille.database import initialize_db
from arseille.vending.vending_machine import VendingMachine


class LifespanState(TypedDict):
    database: AsyncDatabase
    vending_machine: VendingMachine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[LifespanState, None]:
    # Initialize database connection.
    client = await initialize_db()
    database = client[settings.DB_NAME]

    # Create vending machine object.
    vending_machine = VendingMachine()

    yield {
        "database": database,
        "vending_machine": vending_machine,
    }

    print("Releasing resources...")
    # Close database connection.
    await client.close()

    # Release resources used by the vending machine.
    vending_machine.release_resources()

    print("Resources released.")
