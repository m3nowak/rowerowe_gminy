from datetime import datetime
from typing import TypeVar

from .base import BaseStravaModel


class ActivityMap(BaseStravaModel):
    id: str | None
    polyline: str | None
    summary_polyline: str | None


class AthleteReference(BaseStravaModel):
    id: int


class ActivityPartial(BaseStravaModel):
    id: int
    athlete: AthleteReference
    type: str
    sport_type: str
    name: str
    moving_time: int
    elapsed_time: int
    total_elevation_gain: float
    map: ActivityMap | None
    start_date: datetime
    manual: bool
    distance: float
    calories: float
    average_speed: float


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
