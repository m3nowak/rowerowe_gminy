from contextlib import asynccontextmanager
from typing import Annotated

from faststream import ContextRepo, Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

DB_ENGINE_REPO_KEY = "db_engine"
DB_SESSIONMAKER_REPO_KEY = "db_sessionmaker"


def lifespan_factory(db_url: str):
    @asynccontextmanager
    async def lifespan(context: ContextRepo):
        sa_engine = create_async_engine(
            db_url,
        )
        sa_sm = async_sessionmaker(sa_engine, expire_on_commit=False)
        context.set_global(DB_ENGINE_REPO_KEY, sa_engine)
        context.set_global(DB_SESSIONMAKER_REPO_KEY, sa_sm)
        yield
        await sa_engine.dispose()

    return lifespan


async def get_db_session(context: ContextRepo):
    sa_sm: async_sessionmaker = context.get(DB_SESSIONMAKER_REPO_KEY)
    async with sa_sm() as session:
        yield session


async def get_db_engine(context: ContextRepo):
    sa_engine = context.get(DB_ENGINE_REPO_KEY)
    if sa_engine is None:
        raise ValueError("Key not found in context")
    return sa_engine


AsyncSessionDI = Annotated[AsyncSession, Depends(get_db_session)]
AsyncEngineDI = Annotated[AsyncEngine, Depends(get_db_engine)]
