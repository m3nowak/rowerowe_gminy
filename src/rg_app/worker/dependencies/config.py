from contextlib import asynccontextmanager

from faststream import ContextRepo

from rg_app.common.config import BaseConfigModel

CONFIG_REPO_KEY = "config"


def lifespan_factory(config: BaseConfigModel):
    @asynccontextmanager
    async def lifespan(context: ContextRepo):
        context.set_global(CONFIG_REPO_KEY, config)
        yield

    return lifespan


def get_config(context: ContextRepo) -> BaseConfigModel:
    config: BaseConfigModel | None = context.get(CONFIG_REPO_KEY)
    if config is None:
        raise ValueError("Key not found in context")
    return config
