from typing import Literal

from rg_app.common.msg.base_model import BaseModel

# GeoSvcCheckRequest: TypeAlias = dict[str, Any]


class GeoSvcCheckRequest(BaseModel):
    coordinates: list[tuple[float, float]]


class GeoSvcCheckPolylineRequest(BaseModel):
    data: str


class GeoSvcCheckResponseItem(BaseModel):
    id: str
    type: Literal["PAN", "WOJ", "POW", "GMI"]


class GeoSvcCheckResponse(BaseModel):
    items: list[GeoSvcCheckResponseItem]
