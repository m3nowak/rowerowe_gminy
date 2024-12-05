from typing import Self

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from yaml import safe_load


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    @classmethod
    def from_file(cls, path: str) -> Self:
        with open(path) as f:
            return cls(**safe_load(f.read()))
