from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from rg_app.api_worker.config import Config as _Config

_CONFIG_KEY = "config"


def lifespan_factory(config: _Config):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setattr(app.state, _CONFIG_KEY, config)
        yield

    return lifespan


def _provide_config(request: Request) -> _Config:
    return getattr(request.app.state, _CONFIG_KEY)


def get_config_from_app(app: FastAPI) -> _Config:
    if not hasattr(app.state, _CONFIG_KEY):
        raise RuntimeError("Config not set on app")
    return getattr(app.state, _CONFIG_KEY)


Config = Annotated[_Config, Depends(_provide_config)]
