from rg_app.common.config import BaseConfigStruct, BaseDbConfig, BaseNatsConfig, BaseStravaConfig


class Config(BaseConfigStruct):
    strava: BaseStravaConfig
    nats: BaseNatsConfig
    db: BaseDbConfig
