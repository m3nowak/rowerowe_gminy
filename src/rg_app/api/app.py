import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from rg_app.common.fastapi.dependencies.broker import lifespan_factory as broker_lifespan_factory
from rg_app.common.fastapi.dependencies.config import lifespan_factory as config_lifespan_factory
from rg_app.common.fastapi.dependencies.util import combined_lifespans_factory
from rg_app.common.otel.base import prepare_utils

from .config import Config
from .dependencies.db import lifespan_factory as db_lifespan_factory
from .dependencies.debug_flag import lifespan_factory as debug_flag_lifespan_factory
from .dependencies.http_client import lifespan as http_client_lifespan
from .dependencies.strava import lifespan_factory as strava_lifespan_factory
from .routers import activities_router, athletes_router, auth_router, health_router, regions_router, user_router


def app_factory(config: Config, debug: bool = False) -> fastapi.FastAPI:
    mp, tp, lg = prepare_utils(config.otel)
    lifespans = [
        config_lifespan_factory(config),
        db_lifespan_factory(config.db),
        broker_lifespan_factory(mp, tp, lg, config.nats),
        http_client_lifespan,
        strava_lifespan_factory(config.strava),
        debug_flag_lifespan_factory(debug),
    ]

    app = fastapi.FastAPI(title="Rowerowe Gminy API", lifespan=combined_lifespans_factory(*lifespans))
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(regions_router)
    app.include_router(activities_router)
    app.include_router(athletes_router)
    app.include_router(user_router)

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    FastAPIInstrumentor.instrument_app(app, meter_provider=mp, tracer_provider=tp, excluded_urls="health")

    return app
