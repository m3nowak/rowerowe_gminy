from pydantic import Field

from rg_app.common.config import BaseConfigModel, BaseNatsConfig, BaseStravaConfig, CommonSecretType, unpack
from rg_app.common.otel.config import BaseOtelConfig


class NATSConfig(BaseNatsConfig):
    stream: str = "incoming-wha"
    subject_prefix: str = "rg.incoming.wha"
    inbox_prefix: str = "_inbox.wha"


class Config(BaseConfigModel):
    strava: BaseStravaConfig
    self_url: str
    verify_token: CommonSecretType
    nats: NATSConfig
    otel: BaseOtelConfig = Field(default_factory=lambda: BaseOtelConfig())

    def get_verify_token(self) -> str:
        value = unpack(self.verify_token)
        assert value, "Verify token is not set"
        return value
