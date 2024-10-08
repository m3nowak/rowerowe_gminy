from msgspec import Struct

from rg_app.common.msg import BaseStruct


class LoginData(BaseStruct):
    login: str
    password: str


class ActivityMap(Struct):
    id: str | None
    polyline: str | None
    summary_polyline: str | None


class ActivityPartial(Struct):
    type: str
    map: ActivityMap | None
