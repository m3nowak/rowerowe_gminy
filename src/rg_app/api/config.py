import msgspec

from rg_app.api.utils import BaseStruct


class Config(BaseStruct):
    strava_client_id: str
    strava_client_secret: str
    jwt_secret: str
    frontend_url: str

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            return msgspec.yaml.decode(f.read(), type=cls)

    @classmethod
    def dummy(cls) -> "Config":
        return cls(
            strava_client_id="dummy",
            strava_client_secret="dummy",
            jwt_secret="dummy",
            frontend_url="http://localhost:3000",
        )
