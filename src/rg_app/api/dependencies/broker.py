from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from faststream.nats import NatsBroker as _NatsBroker
from nats.aio.client import Client as _NatsClient

from rg_app.api.dependencies.config import get_config_from_app

_BROKER_KEY = "broker"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config_from_app(app)
    broker = _NatsBroker(
        config.nats.url,
        user_credentials=config.nats.creds_path,
        inbox_prefix=config.nats.inbox_prefix,
    )
    await broker.start()
    setattr(app.state, _BROKER_KEY, broker)
    yield
    await broker.close()


def _provide_broker(request: Request) -> _NatsBroker:
    return getattr(request.app.state, _BROKER_KEY)


NatsBroker = Annotated[_NatsBroker, Depends(_provide_broker)]


def _provide_nats_client(broker: NatsBroker) -> _NatsClient:
    if not broker._connection:
        raise RuntimeError("Broker not started")
    return broker._connection


NatsClient = Annotated[_NatsClient, Depends(_provide_nats_client)]


def get_broker_from_app(app: FastAPI) -> _NatsBroker:
    if not hasattr(app.state, _BROKER_KEY):
        raise RuntimeError("Broker not set on app")
    return getattr(app.state, _BROKER_KEY)
