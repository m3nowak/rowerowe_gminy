import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Annotated

from faststream import ContextRepo, Depends
from faststream.nats.annotations import NatsBroker

from rg_app.common.config import BaseStravaConfig
from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.rate_limits import RateLimitManager, RLNatsConfig

from .db import AsyncEngineDI

rlm_lock = asyncio.Lock()
tm_lock = asyncio.Lock()

TOKEN_MGR_REPO_KEY = "token_manager"
RATE_LIMIT_MGR_REPO_KEY = "rate_limit_manager"
STRAVA_EXIT_STACK_REPO_KEY = "strava_exit_stack"
STRAVA_CONFIG_REPO_KEY = "strava_config"


def lifespan_factory(config: BaseStravaConfig):
    @asynccontextmanager
    async def lifespan(context: ContextRepo):
        aes = AsyncExitStack()
        context.set_global(STRAVA_CONFIG_REPO_KEY, config)
        async with aes as aes_activated:
            context.set_global(STRAVA_EXIT_STACK_REPO_KEY, aes_activated)
            yield

    return lifespan


async def get_rate_limit_manager(context: ContextRepo, broker: NatsBroker) -> RateLimitManager:
    async with rlm_lock:
        rate_limit_manager: RateLimitManager | None = context.get(RATE_LIMIT_MGR_REPO_KEY)
        if rate_limit_manager is None:
            # config: BaseStravaConfig = context.get(STRAVA_CONFIG_REPO_KEY)
            aes: AsyncExitStack = context.get(STRAVA_EXIT_STACK_REPO_KEY)
            nats_conn = broker._connection
            if nats_conn is None or not nats_conn.is_connected:
                raise ValueError("NATS connection is not established")
            rlm = RateLimitManager(RLNatsConfig(nats_conn))
            rlm = await aes.enter_async_context(rlm.begin())
            context.set_global(RATE_LIMIT_MGR_REPO_KEY, rlm)
            rate_limit_manager = rlm
    return rate_limit_manager


RateLimitManagerDI = Annotated[RateLimitManager, Depends(get_rate_limit_manager)]


async def get_strava_token_manager(
    context: ContextRepo, rlm: RateLimitManagerDI, engine: AsyncEngineDI
) -> StravaTokenManager:
    async with tm_lock:
        token_manager: StravaTokenManager | None = context.get(TOKEN_MGR_REPO_KEY)
        if token_manager is None:
            config: BaseStravaConfig = context.get(STRAVA_CONFIG_REPO_KEY)
            aes: AsyncExitStack = context.get(STRAVA_EXIT_STACK_REPO_KEY)
            client_secret = config.get_client_secret()
            if client_secret is None:
                raise ValueError("Client secret is not set")
            token_manager = StravaTokenManager(config.client_id, client_secret, rlm, engine)
            token_manager = await aes.enter_async_context(token_manager.begin())
            context.set_global(TOKEN_MGR_REPO_KEY, token_manager)
    return token_manager


StravaTokenManagerDI = Annotated[StravaTokenManager, Depends(get_strava_token_manager)]
