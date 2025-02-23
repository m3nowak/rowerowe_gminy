from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from rg_app.api.config import Config as _Config

_KEY = "debug_flag"


def lifespan_factory(debug: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setattr(app.state, _KEY, debug)
        yield

    return lifespan


def _provide_debug_flag(request: Request) -> _Config:
    return getattr(request.app.state, _KEY)


DebugFlag = Annotated[bool, Depends(_provide_debug_flag)]
