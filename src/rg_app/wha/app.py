from logging import getLogger

import fastapi
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from rg_app.common.fastapi.dependencies.broker import lifespan_factory as broker_lifespan_factory
from rg_app.common.fastapi.dependencies.config import lifespan_factory as config_lifespan_factory
from rg_app.common.fastapi.dependencies.util import combined_lifespans_factory
from rg_app.common.otel.base import prepare_utils

from .config import Config
from .register_sub import lifespan_factory as register_sub_factory
from .router import router


def app_factory(config: Config, debug_mode: bool = False, no_register: bool = False) -> fastapi.FastAPI:
    console_logger = getLogger("console")
    mp, tp, lg = prepare_utils(config.otel)
    lifespans = [
        config_lifespan_factory(config),
        broker_lifespan_factory(mp, tp, lg, config.nats),
    ]
    if not no_register:
        lifespans.append(register_sub_factory(config, logger=console_logger))

    app = fastapi.FastAPI(title="Rowerowe Gminy API", lifespan=combined_lifespans_factory(*lifespans))
    app.include_router(router)

    FastAPIInstrumentor.instrument_app(app, meter_provider=mp, tracer_provider=tp, excluded_urls="health")

    return app
