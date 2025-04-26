import logging
from typing import AsyncContextManager, Callable

from faststream import ContextRepo, FastStream
from faststream.asyncapi import get_app_schema
from faststream.nats import NatsBroker

from rg_app.common.faststream.dep_util import combined_lifespans_factory
from rg_app.common.faststream.otel import prepare_bundle

from .config import Config
from .dependencies.config import lifespan_factory as config_lifespan_factory
from .dependencies.db import lifespan_factory as db_lifespan_factory
from .dependencies.duckdb import lifespan_factory as duckdb_lifespan_factory
from .dependencies.http_client import lifespan as http_client_lifespan
from .dependencies.strava import lifespan_factory as strava_lifespan_factory
from .routers import (
    activity_cmd_router,
    activity_svc_router,
    geo_svc_router,
    user_svc_router,
    webhook_activities_router,
    webhook_revocations_router,
)


def app_factory(config: Config, debug: bool) -> FastStream:
    log_level = logging.DEBUG if debug else logging.INFO
    otel_bundle = prepare_bundle(config.otel)

    lifespans: list[Callable[[ContextRepo], AsyncContextManager[None]]] = [
        config_lifespan_factory(config),
        db_lifespan_factory(config.db.get_url()),
        duckdb_lifespan_factory(config.duck_db_path),
        http_client_lifespan,
        strava_lifespan_factory(config.strava),
    ]
    if otel_bundle:
        lifespans.append(otel_bundle.lifespan)

    broker = NatsBroker(
        config.nats.url,
        log_level=log_level,
        inbox_prefix=config.nats.inbox_prefix,
        user_credentials=config.nats.creds_path,
        middlewares=(otel_bundle.middleware,) if otel_bundle else [],
    )
    broker.include_routers(
        webhook_revocations_router,
        webhook_activities_router,
        activity_cmd_router,
        geo_svc_router,
        activity_svc_router,
        user_svc_router,
    )

    app = FastStream(
        broker,
        lifespan=combined_lifespans_factory(*lifespans),
    )
    return app


def app_schema(config: Config, debug: bool) -> str:
    return get_app_schema(app_factory(config, debug)).to_yaml()
