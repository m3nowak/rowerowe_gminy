from rg_app.common.config import BaseConfigStruct, BaseDbConfig, BaseNatsConfig, SecretReference


class NATSConfig(BaseNatsConfig):
    stream_name: str = "incoming-wha"
    consumer_name: str = "wkk"
    inbox_prefix: str = "_inbox.wkk"
    login_kv = "wkk-auth"
    rate_limits_kv = "rate-limits"


class Config(BaseConfigStruct):
    strava_client_id: str
    strava_client_secret: str | SecretReference
    nats: NATSConfig
    db: BaseDbConfig
    rate_limit_teshold: float = 0.8
    dry_run: bool = False

    def get_strava_client_secret(self) -> str:
        if isinstance(self.strava_client_secret, SecretReference):
            return self.strava_client_secret.value
        else:
            return self.strava_client_secret
