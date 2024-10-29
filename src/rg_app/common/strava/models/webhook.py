from datetime import datetime
from typing import Literal

import pydantic

from .base import BaseStravaModel


class WebhookActivity(BaseStravaModel):
    object_type: Literal["activity"]
    object_id: int
    aspect_type: Literal["create", "update", "delete"]
    event_time: datetime
    owner_id: int
    subscription_id: int
    updates: dict[str, str]

    @pydantic.field_serializer("event_time")
    def serialize_event_time(self, event_time: datetime, _info):
        return int(event_time.timestamp())


class WebhookAthlete(BaseStravaModel):
    object_type: Literal["athlete"]
    object_id: int
    aspect_type: Literal["update"]
    event_time: datetime
    owner_id: int
    subscription_id: int
    updates: dict[str, str]

    @pydantic.field_serializer("event_time")
    def serialize_event_time(self, event_time: datetime, _info):
        return int(event_time.timestamp())
