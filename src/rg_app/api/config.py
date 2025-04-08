from pydantic import Field

from rg_app.common.config import (
    BaseConfigModel,
    BaseDbConfig,
    BaseHttpConfig,
    BaseNatsConfig,
    BaseStravaConfig,
    CommonSecretType,
    unpack_safe,
)
from rg_app.common.otel.config import BaseOtelConfig


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
    origins: list[str] = Field(default_factory=list)
    otel: BaseOtelConfig = Field(default_factory=lambda: BaseOtelConfig())
