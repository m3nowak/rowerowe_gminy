import os.path

from ._config_base import BaseConfigStruct


class SecretReference(BaseConfigStruct):
    """
    SecretReference is a structure that holds a reference to a secret.
    """

    secret_mount_path: str
    secret_key: str

    _value: str | None = None

    @property
    def value(self) -> str:
        """Returns the value of the secret.

        Returns:
            str: The value of the secret.
        """
        if self._value is None:
            with open(os.path.join(self.secret_mount_path, self.secret_key)) as f:
                self._value = f.read().strip()
        return self._value


class BaseStravaConfig(BaseConfigStruct):
    client_id: str
    client_secret: str | SecretReference

    def get_client_secret(self) -> str:
        if isinstance(self.client_secret, SecretReference):
            return self.client_secret.value
        else:
            return self.client_secret


class BaseNatsConfig(BaseConfigStruct):
    url: str | list[str]
    js_domain: str | None = None
    creds_path: str | None = None
    inbox_prefix: str = "_inbox"


class BaseDbConfig(BaseConfigStruct):
    host: str
    port: int
    user: str
    password: str | SecretReference
    database: str

    def get_password(self) -> str:
        if isinstance(self.password, SecretReference):
            return self.password.value
        else:
            return self.password

    def get_url(self, scheme: str = "postgresql+psycopg") -> str:
        return f"{scheme}://{self.user}:{self.get_password()}@{self.host}:{self.port}/{self.database}"


__all__ = ["BaseConfigStruct", "SecretReference", "BaseNatsConfig", "BaseDbConfig"]
