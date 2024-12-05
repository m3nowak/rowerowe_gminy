from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from rg_app.api_worker.config import Config as _Config

from .state import _STATE

_CONFIG_KEY = "config"


def lifespan_factory(config: _Config):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _STATE[_CONFIG_KEY] = config
        # For futurereference, we want to store state this way:
        # setattr(app.state, _CONFIG_KEY, config)
        # https://github.com/airtai/faststream/discussions/1653
        yield

    return lifespan


# def _provide_config(state: State) -> _Config:
#     return state[_CONFIG_KEY]


def _provide_config(request: Request) -> _Config:
    state = request.state
    raise NotImplementedError("This is not implemented yet")
    return state[_CONFIG_KEY]


Config = Annotated[_Config, Depends(_provide_config)]
