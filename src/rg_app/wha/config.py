import msgspec

from rg_app.common.msg import BaseStruct


class NATSConfig(BaseStruct):
    url: str | list[str]
    js_domain: str | None = None
    creds_path: str | None = None
    stream: str = "incoming-wha"
    subject_prefix: str = "rg.incoming.wha"
    inbox_prefix: str = "_inbox.wha"


class Config(BaseStruct):
    strava_client_id: str
    strava_client_secret: str
    self_url: str
    verify_token: str
    nats: NATSConfig

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            return msgspec.yaml.decode(f.read(), type=cls)
