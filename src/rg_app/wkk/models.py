from datetime import datetime
from typing import TypeVar

from msgspec import Struct

from rg_app.common.msg import BaseStruct


class LoginData(BaseStruct):
    login: str
    password: str


class ActivityMap(Struct):
    id: str | None
    polyline: str | None
    summary_polyline: str | None


class ActivityPartial(Struct):
    type: str
    map: ActivityMap | None
    start_date: datetime


T = TypeVar("T")


class ActivityStreamData[T](Struct):
    data: list[T]
    series_type: str
    original_size: int
    resolution: str


class ActivityStreamSet(Struct):
    latlng: ActivityStreamData[tuple[float, float]]
    altitude: ActivityStreamData[float]
    time: ActivityStreamData[int]
