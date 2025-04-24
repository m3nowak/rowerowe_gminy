from contextlib import asynccontextmanager
from logging import Logger
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from faststream.nats import NatsBroker as _NatsBroker
from nats.aio.client import Client as _NatsClient
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

from rg_app.common.config import BaseNatsConfig
from rg_app.common.faststream.otel import direct_prepare_bundle

_BROKER_KEY = "broker"


def lifespan_factory(mp: MeterProvider, tp: TracerProvider, logger: Logger, nats_config: BaseNatsConfig):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bundle = direct_prepare_bundle(mp, tp, logger)
        broker = _NatsBroker(
            nats_config.url,
            user_credentials=nats_config.creds_path,
            inbox_prefix=nats_config.inbox_prefix,
            middlewares=[bundle.middleware],
        )
        await broker.start()
        setattr(app.state, _BROKER_KEY, broker)
        yield
        await broker.close()

    return lifespan


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
