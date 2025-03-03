from datetime import datetime

from rg_app.common.config import BaseConfigModel, BaseDbConfig, BaseNatsConfig, BaseStravaConfig


class NATSConfig(BaseNatsConfig):
    stream_name: str = "incoming-wha"
    consumer_name: str = "wkk"
    inbox_prefix: str = "_inbox.wkk"
    login_kv: str = "wkk-auth"
    rate_limits_kv: str = "rate-limits"


class Config(BaseConfigModel):
    strava: BaseStravaConfig
    nats: NATSConfig
    db: BaseDbConfig
    ignore_before: datetime | None = None
    ignore_after: datetime | None = None
    rate_limit_teshold: float = 0.8
    dry_run: bool = False
