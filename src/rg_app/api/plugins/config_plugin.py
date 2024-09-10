import logging

from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from typing import TypeVar
import msgspec

T = TypeVar("T", bound=msgspec.Struct)

class ConfigPlugin[T](InitPluginProtocol):
    """Plugin for storing application config data"""

    def __init__(self, config_content: T) -> None:
        super().__init__()
        self.config_data = config_content

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        logging.debug(f"Config data loaded by DI: {self.config_data}")
        app_config.dependencies["config"] = Provide(lambda: self.config_data, sync_to_thread=False)
        return app_config
