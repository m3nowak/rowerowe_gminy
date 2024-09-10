from rg_app.api.utils import BaseStruct
import msgspec

class Config(BaseStruct):
    strava_client_id: str
    strava_client_secret: str
    jwt_secret: str
    frontend_url: str

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            return msgspec.yaml.decode(f.read(), type=cls)