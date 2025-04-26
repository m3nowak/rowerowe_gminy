from typing import Annotated

from faststream import Depends
from pydantic import Field

from rg_app.common.config import BaseConfigModel, BaseDbConfig, BaseNatsConfig, BaseStravaConfig
from rg_app.common.otel.config import BaseOtelConfig

from .dependencies.config import get_config


class Config(BaseConfigModel):
    strava: BaseStravaConfig
    nats: BaseNatsConfig
    db: BaseDbConfig
    duck_db_path: str = Field(default="data/geo.db")
    otel: BaseOtelConfig = Field(default_factory=lambda: BaseOtelConfig())


ConfigDI = Annotated[Config, Depends(get_config)]
