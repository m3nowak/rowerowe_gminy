from msgspec import field

from rg_app.common.config import BaseConfigStruct, BaseDbConfig, BaseNatsConfig, BaseStravaConfig
from rg_app.common.otel.config import BaseOtelConfig


class Config(BaseConfigStruct):
    strava: BaseStravaConfig
    nats: BaseNatsConfig
    db: BaseDbConfig
    duck_db_path: str = field(default="data/geo.db")
    otel: BaseOtelConfig = field(default_factory=lambda: BaseOtelConfig())
