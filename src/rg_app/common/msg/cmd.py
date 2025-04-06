from datetime import datetime
from typing import Literal

from pydantic import Field

from rg_app.common.strava.models.activity import ActivityPartial

from .base_model import BaseModel


class StdActivityCmd(BaseModel):
    owner_id: int
    activity_id: int
    type: Literal["create", "update", "delete"]
    activity: ActivityPartial | None = None
    is_from_backlog: bool = False


class BacklogActivityCmd(BaseModel):
    owner_id: int
    period_from: datetime
    period_to: datetime
    type: Literal["backlog"] = Field("backlog")
