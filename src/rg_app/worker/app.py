import logging
from typing import Any, Awaitable, Callable

from faststream import FastStream
from faststream.asyncapi import get_app_schema
from faststream.nats import NatsBroker

from rg_app.common.faststream.otel import prepare_bundle

from .config import Config
from .deps import after_startup, lifespan, on_startup_factory
from .routers import activity_cmd_router, geo_svc_router, incoming_wha_router


def app_factory(config: Config, debug: bool) -> FastStream:
    log_level = logging.DEBUG if debug else logging.INFO
    otel_bundle = prepare_bundle(config.otel)
    broker = NatsBroker(
        config.nats.url,
        log_level=log_level,
        inbox_prefix=config.nats.inbox_prefix,
        user_credentials=config.nats.creds_path,
        middlewares=(otel_bundle.middeware,) if otel_bundle else [],
    )
    broker.include_routers(incoming_wha_router, activity_cmd_router, geo_svc_router)

    on_startup: list[Callable[..., Awaitable[Any]]] = [on_startup_factory(config)]
    if otel_bundle:
        on_startup.append(otel_bundle.on_startup)

    app = FastStream(
        broker,
        on_startup=on_startup,
        after_startup=[after_startup],  # type: ignore
        lifespan=lifespan,
    )
    return app


def app_schema(config: Config, debug: bool) -> str:
    return get_app_schema(app_factory(config, debug)).to_yaml()
