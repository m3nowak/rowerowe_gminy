from contextlib import AsyncExitStack
from dataclasses import dataclass

from httpx import AsyncClient
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from nats.aio.client import Client as NatsClient
from sqlalchemy.ext.asyncio import AsyncEngine

from rg_app.common.strava import RateLimitManager, RLNatsConfig, StravaTokenManager

_STRAVA_URL = "https://www.strava.com/api/v3"


RATE_LIMITS_KWARG = "rate_limits"
TOKEN_MGR_KWARG = "strava_token_mgr"


@dataclass
class StravaPluginConfig:
    client_id: str
    client_secret: str
    url: str = _STRAVA_URL
    rate_limits_kv: str = "rate-limits"


class StravaPlugin(InitPluginProtocol):
    """NATS plugin for Litestar"""

    def __init__(self, sp_cfg: StravaPluginConfig) -> None:
        super().__init__()
        self.cfg = sp_cfg
        self._token_mgr: StravaTokenManager | None = None
        self._rate_limit_mgr: RateLimitManager | None = None
        self._client: AsyncClient | None = None

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        # app_config.lifespan.append(self._token_mgr.begin())

        async def provide_token_mgr(
            rate_limits: RateLimitManager, async_exit_stack: AsyncExitStack, db_engine: AsyncEngine
        ) -> StravaTokenManager:
            if self._token_mgr is None:
                tm = StravaTokenManager(self.cfg.client_id, self.cfg.client_secret, rate_limits, db_engine)
                self._token_mgr = await async_exit_stack.enter_async_context(tm.begin())
            return self._token_mgr

        async def provide_rate_limit_mgr(nats: NatsClient, async_exit_stack: AsyncExitStack) -> RateLimitManager:
            if self._rate_limit_mgr is None:
                rlm = RateLimitManager(RLNatsConfig(nats))
                self._rate_limit_mgr = await async_exit_stack.enter_async_context(rlm.begin())
            return self._rate_limit_mgr

        app_config.dependencies[TOKEN_MGR_KWARG] = Provide(provide_token_mgr)
        app_config.dependencies[RATE_LIMITS_KWARG] = Provide(provide_rate_limit_mgr)

        return app_config
