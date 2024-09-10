from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol


class DiFiller(InitPluginProtocol):
    """Plugin for filling DI container with empty dependencies"""

    def __init__(self, keys: list[str]) -> None:
        super().__init__()
        self.keys = keys

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        for key in self.keys:
            app_config.dependencies[key] = Provide(lambda: None, sync_to_thread=False)
        return app_config
