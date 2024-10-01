from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from httpx import AsyncClient
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from strava_api import Client as StravaClient

from rg_app.common.strava import StravaTokenManager

_STRAVA_URL = "https://www.strava.com/api/v3"


@dataclass
class StravaPluginConfig:
    client_id: str
    client_secret: str
    token_mgr_kwarg: str = "strava_token_mgr"
    api_client_kwarg: str = "strava_client"
    url: str = _STRAVA_URL


class StravaPlugin(InitPluginProtocol):
    """NATS plugin for Litestar"""

    def __init__(self, sp_cfg: StravaPluginConfig) -> None:
        super().__init__()
        self.cfg = sp_cfg
        self._token_mgr = StravaTokenManager(sp_cfg.client_id, sp_cfg.client_secret)
        self._client: AsyncClient | None = None

    @asynccontextmanager
    async def client_ctx(self) -> AsyncGenerator[AsyncClient, None]:
        strava_client = StravaClient(self.cfg.url)
        async with strava_client.get_async_httpx_client() as client:
            try:
                self._client = client
                yield client
            finally:
                pass

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.lifespan.append(self._token_mgr.begin())
        app_config.lifespan.append(self.client_ctx())

        def provide_token_mgr() -> StravaTokenManager:
            return self._token_mgr

        def provide_client() -> AsyncClient:
            assert self._client is not None
            return self._client

        app_config.dependencies[self.cfg.token_mgr_kwarg] = Provide(provide_token_mgr, sync_to_thread=False)
        app_config.dependencies[self.cfg.api_client_kwarg] = Provide(provide_client, sync_to_thread=False)
        return app_config
