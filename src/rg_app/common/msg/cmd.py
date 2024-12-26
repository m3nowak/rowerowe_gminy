from datetime import datetime
from typing import Literal

from pydantic import Field

from .base_model import BaseModel


class StdActivityCmd(BaseModel):
    owner_id: int
    activity_id: int
    type: Literal["create", "update", "delete"]


class BacklogActivityCmd(BaseModel):
    owner_id: int
    period_from: datetime
    period_to: datetime
    type: Literal["backlog"] = Field("backlog")
