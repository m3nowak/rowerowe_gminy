from rg_app.common.config import BaseConfigStruct, BaseDbConfig, BaseNatsConfig, SecretReference


class NATSConfig(BaseNatsConfig):
    consumer_deliver_subject: str = "rg.consumer.wkk"
    inbox_prefix: str = "_inbox.wkk"
    login_kv = "wkk-auth"


class Config(BaseConfigStruct):
    strava_client_id: str
    strava_client_secret: str | SecretReference
    nats: NATSConfig
    db: BaseDbConfig

    def get_strava_client_secret(self) -> str:
        if isinstance(self.strava_client_secret, SecretReference):
            return self.strava_client_secret.value
        else:
            return self.strava_client_secret
