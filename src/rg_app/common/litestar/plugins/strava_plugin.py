from dataclasses import dataclass

from httpx import AsyncClient
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol

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

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.lifespan.append(self._token_mgr.begin())

        def provide_token_mgr() -> StravaTokenManager:
            return self._token_mgr

        app_config.dependencies[self.cfg.token_mgr_kwarg] = Provide(provide_token_mgr, sync_to_thread=False)
        return app_config
