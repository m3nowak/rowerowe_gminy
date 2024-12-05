import fastapi

from .config import Config
from .dependencies.config import lifespan_factory
from .http import router as http_router
from .nats import router_factory as nats_router_factory


def app_factory(config: Config):
    app = fastapi.FastAPI(title="Rowerowe Gminy API", lifespan=lifespan_factory(config))

    app.include_router(http_router)
    if config.nats:
        app.include_router(nats_router_factory(config.nats, app.state))

    return app
