# from rg_app.common.msg import BaseStruct
from typing import Any

from msgspec import Struct


class StravaEvent(Struct):
    object_type: str
    object_id: int
    aspect_type: str
    event_time: int
    owner_id: int
    subscription_id: int
    updates: dict[str, Any] | None = None
