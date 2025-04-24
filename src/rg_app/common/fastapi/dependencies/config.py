from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from rg_app.common.config import BaseConfigModel

_CONFIG_KEY = "config"


def lifespan_factory(config: BaseConfigModel):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setattr(app.state, _CONFIG_KEY, config)
        yield

    return lifespan


def provide_config(request: Request) -> BaseConfigModel:
    return getattr(request.app.state, _CONFIG_KEY)


def get_config_from_app(app: FastAPI) -> BaseConfigModel:
    if not hasattr(app.state, _CONFIG_KEY):
        raise RuntimeError("Config not set on app")
    return getattr(app.state, _CONFIG_KEY)
