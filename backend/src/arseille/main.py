from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from arseille.lifespan import lifespan
from arseille.vending.routes import router

app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"operationsSorter": "method"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates("static")

app.include_router(router=router)


@app.get("/vending-machine", response_class=HTMLResponse)
def vending_machine(request: Request, mode: int) -> Any:
    return templates.TemplateResponse(
        request=request, name="index.html", context={"mode": mode}
    )


@app.get("/vending-machine/simulation", response_class=HTMLResponse)
def vending_machine_simulation(request: Request) -> Any:
    return templates.TemplateResponse(request=request, name="simulation.html")


@app.get("/", response_class=PlainTextResponse)
async def root() -> Any:
    return "Hello World"
