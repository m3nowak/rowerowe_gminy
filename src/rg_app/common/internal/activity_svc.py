from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

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

    track_is_detailed: bool

    elevation_gain: Optional[Decimal] = None
    elevation_low: Optional[Decimal] = None
    elevation_high: Optional[Decimal] = None

    sport_type: str
    gear_id: Optional[str] = None

    polyline: str
    full_data: dict[str, Any] | None = None


class UpsertModelIneligible(BaseModel):
    id: int
    user_id: int
    name: str
    reject_reason: str
    start: datetime
