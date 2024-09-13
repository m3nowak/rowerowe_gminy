import msgspec

from rg_app.common.msg import BaseStruct

class NATSConfig(BaseStruct):
    url: str| list[str]
    js_domain: str

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
