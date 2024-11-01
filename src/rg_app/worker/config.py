from msgspec import field

from rg_app.common.config import BaseConfigStruct, BaseDbConfig, BaseNatsConfig, BaseOtelConfig, BaseStravaConfig


class Config(BaseConfigStruct):
    strava: BaseStravaConfig
    nats: BaseNatsConfig
    db: BaseDbConfig
    otel: BaseOtelConfig = field(default_factory=lambda: BaseOtelConfig())
