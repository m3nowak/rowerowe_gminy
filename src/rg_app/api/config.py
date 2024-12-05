from pydantic import SecretStr

from rg_app.common.config import BaseConfigModel, BaseDbConfig, BaseNatsConfig, CommonSecretType, unpack


class NatsConfig(BaseNatsConfig):
    rate_limits_kv = "rate-limits"


class Config(BaseConfigModel):
    strava_client_id: str
    strava_client_secret: CommonSecretType
    jwt_secret: CommonSecretType
    frontend_url: str
    db: BaseDbConfig
    nats: NatsConfig
    login_url: str = "/authenticate/login"

    def get_strava_client_secret(self) -> str:
        value = unpack(self.strava_client_secret)
        assert value, "Strava client secret is not set"
        return value

    def get_jwt_secret(self) -> str:
        value = unpack(self.jwt_secret)
        assert value, "JWT secret is not set"
        return value

    @classmethod
    def dummy(cls) -> "Config":
        return cls(
            strava_client_id="dummy",
            strava_client_secret=SecretStr("dummy"),
            jwt_secret=SecretStr("dummy"),
            frontend_url="http://localhost:3000",
            db=BaseDbConfig(
                host="localhost",
                port=5432,
                database="rg",
                user="rg",
                password=SecretStr("rg"),
            ),
            nats=NatsConfig(url="nats://localhost"),
        )
