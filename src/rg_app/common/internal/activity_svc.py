from datetime import datetime
from decimal import Decimal
from typing import Optional

from rg_app.common.msg.base_model import BaseModel


class DeleteModel(BaseModel):
    id: int
    user_id: int


class UpsertModel(BaseModel):
    id: int
    user_id: int
    name: str
    manual: bool

    start: datetime
    moving_time: int
    elapsed_time: int
    distance: Decimal

    track: list[tuple[float, float]]
    track_is_detailed: bool

    elevation_gain: Optional[Decimal] = None
    elevation_low: Optional[Decimal] = None
    elevation_high: Optional[Decimal] = None

    type: str
    sport_type: Optional[str] = None
    gear_id: Optional[str] = None

    visited_regions: list[str]
    visited_regions_additional: list[str]
