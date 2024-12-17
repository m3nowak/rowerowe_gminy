from rg_app.common.config import (
    BaseConfigModel,
    BaseDbConfig,
    BaseHttpConfig,
    BaseNatsConfig,
    BaseStravaConfig,
    CommonSecretType,
    unpack_safe,
)


class NatsConfig(BaseNatsConfig):
    pass


class AuthConfig(BaseConfigModel):
    standard_expiry_hours: int = 24
    long_expiry_hours: int = 24 * 30
    secret: CommonSecretType

    def get_secret(self) -> str:
        return unpack_safe(self.secret)


class Config(BaseConfigModel):
    http: BaseHttpConfig
    nats: NatsConfig
    strava: BaseStravaConfig
    db: BaseDbConfig
    auth: AuthConfig
