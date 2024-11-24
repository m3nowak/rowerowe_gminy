from typing import Any, Literal, TypeAlias

from rg_app.common.msg.base_model import BaseModel

GeoSvcCheckRequest: TypeAlias = dict[str, Any]


class GeoSvcCheckResponseItem(BaseModel):
    id: str
    type: Literal["PAN", "WOJ", "POW", "GMI"]


class GeoSvcCheckResponse(BaseModel):
    items: list[GeoSvcCheckResponseItem]
