from pydantic import Field

from rg_app.common.config import BaseConfigModel, BaseDbConfig, BaseNatsConfig, BaseStravaConfig
from rg_app.common.otel.config import BaseOtelConfig


class Config(BaseConfigModel):
    strava: BaseStravaConfig
    nats: BaseNatsConfig
    db: BaseDbConfig
    duck_db_path: str = Field(default="data/geo.db")
    otel: BaseOtelConfig = Field(default_factory=lambda: BaseOtelConfig())
