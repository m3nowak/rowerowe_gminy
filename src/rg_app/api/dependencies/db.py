from contextlib import asynccontextmanager
from typing import Annotated

import sqlalchemy.ext.asyncio as sa_async
from fastapi import Depends, FastAPI, Request

from rg_app.common.config import BaseDbConfig

_ENGINE_KEY = "SQLALCHEMY_ENGINE"
_SESSIONMAKER_KEY = "SQLALCHEMY_SESSIONMAKER"


def lifespan_factory(config_db: BaseDbConfig):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = sa_async.create_async_engine(config_db.get_url())
        sessionmaker = sa_async.async_sessionmaker(bind=engine)
        setattr(app.state, _ENGINE_KEY, engine)
        setattr(app.state, _SESSIONMAKER_KEY, sessionmaker)
        yield
        await engine.dispose()

    return lifespan


async def _provide_session(request: Request):
    app = request.app
    sessionmaker: sa_async.async_sessionmaker[sa_async.AsyncSession] = getattr(app.state, _SESSIONMAKER_KEY)
    async with sessionmaker() as session:
        yield session


AsyncSession = Annotated[sa_async.AsyncSession, Depends(_provide_session)]


async def _provide_engine(request: Request):
    app = request.app
    engine: sa_async.AsyncEngine = getattr(app.state, _ENGINE_KEY)
    yield engine


AsyncEngine = Annotated[sa_async.AsyncEngine, Depends(_provide_engine)]


def get_engine_from_app(app: FastAPI) -> sa_async.AsyncEngine:
    if not hasattr(app.state, _ENGINE_KEY):
        raise RuntimeError("Engine not set on app")
    return getattr(app.state, _ENGINE_KEY)
