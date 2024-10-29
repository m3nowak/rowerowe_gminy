import logging

from faststream import FastStream
from faststream.asyncapi import get_app_schema
from faststream.nats import NatsBroker

from .config import Config
from .deps import after_startup, lifespan, on_startup_factory
from .routers import incoming_wha_router


def app_factory(config: Config, debug: bool) -> FastStream:
    log_level = logging.DEBUG if debug else logging.INFO
    broker = NatsBroker(
        config.nats.url,
        log_level=log_level,
        inbox_prefix=config.nats.inbox_prefix,
        user_credentials=config.nats.creds_path,
    )
    broker.include_routers(incoming_wha_router)

    app = FastStream(
        broker,
        on_startup=[on_startup_factory(config)],
        after_startup=[after_startup],  # type: ignore
        lifespan=lifespan,
    )
    return app


def app_schema(config: Config, debug: bool) -> str:
    return get_app_schema(app_factory(config, debug)).to_yaml()
