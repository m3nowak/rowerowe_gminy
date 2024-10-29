from datetime import datetime
from typing import TypeVar

from .base import BaseStravaModel


class ActivityMap(BaseStravaModel):
    id: str | None
    polyline: str | None
    summary_polyline: str | None


class ActivityPartial(BaseStravaModel):
    type: str
    map: ActivityMap | None
    start_date: datetime


T = TypeVar("T")


class ActivityStreamData[T](BaseStravaModel):
    data: list[T]
    series_type: str
    original_size: int
    resolution: str


class ActivityStreamSet(BaseStravaModel):
    latlng: ActivityStreamData[tuple[float, float]]
    altitude: ActivityStreamData[float]
    time: ActivityStreamData[int]
