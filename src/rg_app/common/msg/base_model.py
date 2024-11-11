from typing import Any

import pydantic
from pydantic.alias_generators import to_camel


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True, alias_generator=to_camel)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs: Any) -> str:
        kwargs.setdefault("by_alias", True)
        return super().model_dump_json(**kwargs)
