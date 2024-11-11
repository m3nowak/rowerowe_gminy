from datetime import datetime
from typing import Literal

from pydantic import Field

from .base_model import BaseModel


class CreateActivityCmd(BaseModel):
    owner_id: int
    activity_id: int
    type: Literal["create"] = Field("create")


class UpdateActivityCmd(BaseModel):
    owner_id: int
    activity_id: int
    type: Literal["update"] = Field("update")


class DeleteActivityCmd(BaseModel):
    owner_id: int
    activity_id: int
    type: Literal["delete"] = Field("delete")


class BacklogActivityCmd(BaseModel):
    owner_id: int
    perioid_from: datetime
    perioid_to: datetime
    type: Literal["backlog"] = Field("backlog")
