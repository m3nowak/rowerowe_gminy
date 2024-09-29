import msgspec

from rg_app.common.config import BaseConfigStruct, SecretReference


class Config(BaseConfigStruct):
    strava_client_id: str
    strava_client_secret: str | SecretReference
    jwt_secret: str | SecretReference
    frontend_url: str
    db_url: str | SecretReference

    def get_strava_client_secret(self) -> str:
        if isinstance(self.strava_client_secret, SecretReference):
            return self.strava_client_secret.value
        return self.strava_client_secret
    
    def get_jwt_secret(self) -> str:
        if isinstance(self.jwt_secret, SecretReference):
            return self.jwt_secret.value
        return self.jwt_secret
    
    def get_db_url(self) -> str:
        if isinstance(self.db_url, SecretReference):
            return self.db_url.value
        return self.db_url

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
            db_url="sqlite+aiosqlite:///async.sqlite",
        )
