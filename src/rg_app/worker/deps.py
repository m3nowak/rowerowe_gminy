import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from faststream import ContextRepo
from faststream.nats.annotations import NatsBroker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.rate_limits import RateLimitManager, RLNatsConfig

from .config import Config


@asynccontextmanager
async def lifespan(context: ContextRepo):
    exit_stack = AsyncExitStack()
    async with exit_stack as aes:
        context.set_global("exit_stack", aes)
        yield


def on_startup_factory(config: Config):
    async def on_startup(context: ContextRepo):
        context.set_global("config", config)
        aes: AsyncExitStack = context.get("exit_stack")

        http_client = AsyncClient()
        http_client = await aes.enter_async_context(http_client)
        context.set_global("http_client", http_client)

        sa_engine = create_async_engine(
            config.db.get_url(),
        )
        aes.push_async_callback(sa_engine.dispose)
        sa_sm = async_sessionmaker(sa_engine, expire_on_commit=False)
        context.set_global("sa_engine", sa_engine)
        context.set_global("sa_sm", sa_sm)

    return on_startup


async def after_startup(context: ContextRepo, broker: NatsBroker):
    config: Config = context.get("config")
    nats_connection = broker._connection
    assert nats_connection is not None
    aes = context.get("exit_stack")
    sa_engine = context.get("sa_engine")

    rlm = RateLimitManager(RLNatsConfig(nats_connection))
    rlm = await aes.enter_async_context(rlm.begin())
    context.set_global("rate_limit_mgr", rlm)

    stm = StravaTokenManager(config.strava.client_id, config.strava.get_client_secret(), rlm, sa_engine)
    stm = await aes.enter_async_context(stm.begin())
    context.set_global("strava_token_mgr", stm)


async def db_session(context: ContextRepo):
    sa_sm: async_sessionmaker = context.get("sa_sm")
    async with sa_sm() as session:
        yield session


async def _get_context_var_delayed(context: ContextRepo, var_name: str, delay: float = 1.0):
    var = context.get(var_name)
    if var is None:
        # looks like after_startup is not called yet
        await asyncio.sleep(delay)
        var = context.get(var_name)
        if var is None:
            raise ValueError(f"Failed to get {var_name} from ContextRepo")
    return var


async def token_mgr(context: ContextRepo) -> StravaTokenManager:
    return await _get_context_var_delayed(context, "strava_token_mgr")


async def rate_limit_mgr(context: ContextRepo) -> RateLimitManager:
    return await _get_context_var_delayed(context, "rate_limit_mgr")


async def http_client(context: ContextRepo):
    http_client = context.get("http_client")
    return http_client
