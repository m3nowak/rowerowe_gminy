import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .config import Config
from .dependencies.broker import lifespan as broker_lifespan
from .dependencies.config import lifespan_factory as config_lifespan_factory
from .dependencies.db import lifespan as db_lifespan
from .dependencies.http_client import lifespan as http_client_lifespan
from .dependencies.strava import lifespan as strava_lifespan
from .dependencies.util import combined_lifespans_factory
from .routers import activities_router, auth_router, health_router, regions_router


def app_factory(config: Config):
    lifespans = [
        config_lifespan_factory(config),
        db_lifespan,
        broker_lifespan,
        http_client_lifespan,
        strava_lifespan,
    ]

    app = fastapi.FastAPI(title="Rowerowe Gminy API", lifespan=combined_lifespans_factory(*lifespans))
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(regions_router)
    app.include_router(activities_router)

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    return app
