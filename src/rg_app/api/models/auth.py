from enum import StrEnum
from typing import Literal, Sequence

from pydantic import Field

from rg_app.common.msg.base_model import BaseModel


class StravaScopes(StrEnum):
    READ = "read"
    READ_ALL = "read_all"
    PROFILE_READ_ALL = "profile:read_all"
    PROFILE_WRITE = "profile:write"
    ACTIVITY_READ = "activity:read"
    ACTIVITY_READ_ALL = "activity:read_all"
    ACTIVITY_WRITE = "activity:write"


class LoginRequest(BaseModel):
    code: str
    scopes: Sequence[StravaScopes]
    remember_longer: bool = False


class LoginResponse(BaseModel):
    access_token: str = Field(alias="access_token")
    token_type: Literal["bearer"] = Field("bearer", alias="token_type")
    is_first_login: bool


class LoginErrorCause(StrEnum):
    INVALID_SCOPE = "invalid_scope"
    INVALID_CODE = "invalid_code"
    STRAVA_ERROR = "strava_error"
    INTERNAL_ERROR = "internal_error"


class LoginResponseError(BaseModel):
    cause: LoginErrorCause
