from contextlib import AsyncExitStack, asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from rg_app.common.strava import RateLimitManager as _RateLimitManager
from rg_app.common.strava import RLNatsConfig
from rg_app.common.strava import StravaTokenManager as _StravaTokenManager

from .broker import get_broker_from_app
from .config import get_config_from_app
from .db import get_engine_from_app

_STRAVA_TOKEN_MANAGER_KEY = "strava_token_manager"
_RATE_LIMIT_MANAGER_KEY = "rate_limit_manager"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config_from_app(app)
    broker = get_broker_from_app(app)
    engine = get_engine_from_app(app)
    conn = broker._connection
    assert conn is not None
    async with AsyncExitStack() as aes:
        rlm = _RateLimitManager(RLNatsConfig(conn))
        rlm = await aes.enter_async_context(rlm.begin())
        setattr(app.state, _RATE_LIMIT_MANAGER_KEY, rlm)

        client_secret = config.strava.get_client_secret()
        assert client_secret is not None

        stm = _StravaTokenManager(
            config.strava.client_id,
            client_secret,
            rlm,
            engine,
        )
        stm = await aes.enter_async_context(stm.begin())
        setattr(app.state, _STRAVA_TOKEN_MANAGER_KEY, stm)
        yield


async def provide_strava_token_manager(request: Request):
    return getattr(request.app.state, _STRAVA_TOKEN_MANAGER_KEY)


async def provide_rate_limit_manager(request: Request):
    return getattr(request.app.state, _RATE_LIMIT_MANAGER_KEY)


StravaTokenManager = Annotated[_StravaTokenManager, Depends(provide_strava_token_manager)]
RateLimitManager = Annotated[_RateLimitManager, Depends(provide_rate_limit_manager)]
