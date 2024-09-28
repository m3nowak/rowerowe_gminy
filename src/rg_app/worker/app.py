import logging

from faststream import FastStream
from faststream.nats import NatsBroker

from .config import Config
from .routers import echo_router, stream_router


def app_factory(config: Config, debug: bool) -> FastStream:
    log_level = logging.DEBUG if debug else logging.INFO
    broker = NatsBroker(
        config.nats.url,
        log_level=log_level,
        inbox_prefix=config.nats.inbox_prefix,
        user_credentials=config.nats.creds_path,
        pedantic=True,
    )
    broker.include_routers(echo_router, stream_router)

    app = FastStream(broker)
    app.logger
    return app
