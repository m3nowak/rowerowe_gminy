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
    perioid_from: datetime
    perioid_to: datetime
    type: Literal["backlog"] = Field("backlog")
