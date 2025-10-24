from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from arseille.lifespan import lifespan

app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"operationsSorter": "method"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse)
async def root() -> Any:
    return "Hello World"
