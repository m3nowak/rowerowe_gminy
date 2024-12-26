from typing import Sequence, TypeVar

import pydantic


class BaseStravaModel(pydantic.BaseModel):
    pass


T = TypeVar("T")


class PaginatedResult[T](BaseStravaModel):
    items: Sequence[T]
    page: int
    has_more: bool
