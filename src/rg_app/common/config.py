import os
from typing import TypeVar

from pydantic import SecretStr

from ._config_base import BaseConfigModel

SN = TypeVar("SN", bound=str | None)


class EnvReference(BaseConfigModel):
    """
    EnvReference is a structure that holds a reference to an environment variable.
    """

    env: str

    def get_value(self, default: SN = None) -> str | SN:
        return os.environ.get(self.env, default)


class SecretReference(BaseConfigModel):
    """
    SecretReference is a structure that holds a reference to a secret.
    """

    secret_mount_path: str
    secret_key: str

    def get_value(self, default: SN = None) -> str | SN:
        if os.path.exists(os.path.join(self.secret_mount_path, self.secret_key)):
            with open(os.path.join(self.secret_mount_path, self.secret_key)) as f:
                return f.read().strip()
        else:
            return default


CommonSecretType = SecretStr | SecretReference | EnvReference


def unpack(value: str | SecretStr | SecretReference | EnvReference, default: SN = None) -> str | SN:
    if isinstance(value, (SecretReference, EnvReference)):
        return value.get_value(default)
    elif isinstance(value, SecretStr):
        return value.get_secret_value()
    else:
        return value


class BaseStravaConfig(BaseConfigModel):
    client_id: str
    client_secret: SecretStr | SecretReference | EnvReference

    def get_client_secret(self) -> str | None:
        return unpack(self.client_secret)


class BaseNatsConfig(BaseConfigModel):
    url: str | list[str]
    js_domain: str | None = None
    creds_path: str | None = None
    inbox_prefix: str = "_inbox"


class BaseHttpConfig(BaseConfigModel):
    host: str = "0.0.0.0"
    port: int = 8000


class BaseDbConfig(BaseConfigModel):
    host: str
    port: int
    user: str
    password: SecretStr | SecretReference | EnvReference
    database: str

    def get_password(self) -> str | None:
        return unpack(self.password)

    def get_url(self, scheme: str = "postgresql+psycopg") -> str:
        password = self.get_password()
        assert password, "Password is not set"
        return f"{scheme}://{self.user}:{password}@{self.host}:{self.port}/{self.database}"


__all__ = [
    "SecretReference",
    "BaseNatsConfig",
    "BaseDbConfig",
    "unpack",
    "BaseStravaConfig",
    "CommonSecretType",
    "EnvReference",
]
