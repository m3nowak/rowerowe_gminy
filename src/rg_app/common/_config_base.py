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
