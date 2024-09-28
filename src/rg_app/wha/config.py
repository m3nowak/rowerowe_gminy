from rg_app.common.config import BaseConfigStruct, SecretReference


class NATSConfig(BaseConfigStruct):
    url: str | list[str]
    js_domain: str | None = None
    creds_path: str | None = None
    stream: str = "incoming-wha"
    subject_prefix: str = "rg.incoming.wha"
    inbox_prefix: str = "_inbox.wha"


class Config(BaseConfigStruct):
    strava_client_id: str
    strava_client_secret: str | SecretReference
    self_url: str
    verify_token: str | SecretReference
    nats: NATSConfig

    def get_strava_client_secret(self) -> str:
        if isinstance(self.strava_client_secret, SecretReference):
            return self.strava_client_secret.value
        else:
            return self.strava_client_secret

    def get_verify_token(self) -> str:
        if isinstance(self.verify_token, SecretReference):
            return self.verify_token.value
        else:
            return self.verify_token
