import os.path
from typing import Self

import msgspec


class BaseConfigStruct(msgspec.Struct, rename="camel"):
    """
    BaseConfigStruct is a base configuration structure that inherits from msgspec.Struct
    and uses camel case renaming for its fields.
    """

    @classmethod
    def from_file(cls, path: str) -> Self:
        """Reads a configuration file and returns an instance of the class.

        Args:
            path (str): The path to the configuration file.

        Returns:
            Self: An instance of the class.
        """
        with open(path) as f:
            return msgspec.yaml.decode(f.read(), type=cls)


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
