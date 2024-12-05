from rg_app.common.config import BaseConfigModel, BaseHttpConfig, BaseNatsConfig, BaseStravaConfig


class NatsConfig(BaseNatsConfig):
    pass


class Config(BaseConfigModel):
    http: BaseHttpConfig
    nats: NatsConfig | None = None
    strava: BaseStravaConfig | None = None
    tlo: str = "tlo"
