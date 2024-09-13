import os
import typing as ty
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import httpx
import msgspec
from litestar import post
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.api.config import Config
from rg_app.common.msg import BaseStruct
from rg_app.db import User


class StravaAuthResponse(msgspec.Struct):
    token_type: ty.Literal["Bearer"]
    expires_at: int
    expires_in: int
    refresh_token: str
    access_token: str
    athlete: dict[str, ty.Any]

    def make_username(self) -> str:
        if self.athlete.get("firstname") is not None or self.athlete.get("lastname") is not None:
            snc = [self.athlete.get("firstname"), self.athlete.get("lastname")]
            snc = list(filter(lambda x: x is not None, snc))
            return " ".join(snc)  # type: ignore
        elif self.athlete.get("username") is not None:
            return self.athlete["username"]
        else:
            return str(self.athlete["id"])


class StravaScopes(StrEnum):
    READ = "read"
    READ_ALL = "read_all"
    PROFILE_READ_ALL = "profile:read_all"
    PROFILE_WRITE = "profile:write"
    ACTIVITY_READ = "activity:read"
    ACTIVITY_READ_ALL = "activity:read_all"
    ACTIVITY_WRITE = "activity:write"


"""Example response
  {
  "token_type": "Bearer",
  "expires_at": 1725926700, #unix ts
  "expires_in": 21364,
  "refresh_token": "<reftoken>", #40char 0-9a-f
  "access_token": "<acctoken>", #40char 0-9a-f
  "athlete": {
    "id": user_id, # int, a long one,
    "username": null,
    "resource_state": 2,
    "firstname": "Fname",
    "lastname": "Lname",
    "bio": "",
    "city": "City",
    "state": "",
    "country": null,
    "sex": "M",
    "premium": true,
    "summit": true,
    "created_at": "2021-05-14T09:51:32Z",
    "updated_at": "2024-09-09T20:14:11Z",
    "badge_type_id": 1,
    "weight": 90,
    "profile_medium": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/user_id/probablyimageid/1/medium.jpg",
    "profile": "https://dgalywyr863hv.cloudfront.net/pictures/athletes/user_id/probablyimageid/1/large.jpg",
    "friend": null,
    "follower": null
  }
}
"""


class AuthRequest(BaseStruct):
    code: str
    scopes: ty.List[StravaScopes]
    remember_longer: bool = False


class MinimalUser(BaseStruct):
    id: int


class AuthResponse(BaseStruct):
    token: str
    user: MinimalUser
    some_example_data: str | None = None


async def retrieve_user_handler(
    token: Token, connection: "ASGIConnection[ty.Any, ty.Any, ty.Any, ty.Any]"
) -> ty.Optional[MinimalUser]:
    return MinimalUser(id=int(token.sub))


jwt_auth = JWTAuth[MinimalUser](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=os.environ.get("JWT_SECRET", "abcd123"),
    exclude=["/authenticate", "/docs"],
)


async def authenticate(code: str, config: Config) -> StravaAuthResponse | None:
    data_dict = {
        "client_id": config.strava_client_id,
        "client_secret": config.strava_client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("https://www.strava.com/oauth/token", data=data_dict)
        if r.is_error:
            return None
        sar = msgspec.json.decode(r.text, type=StravaAuthResponse)
        return sar


@post(
    "/authenticate", tags=["auth"], description="Authenticate with Strava with provided code", status_code=HTTP_200_OK
)
async def authenticate_handler(data: AuthRequest, config: Config, db_session: AsyncSession) -> AuthResponse:
    sar = await authenticate(data.code, config)
    assert sar is not None
    user_id: int | None = sar.athlete.get("id")
    assert user_id is not None

    user = await db_session.get(User, user_id)
    if user:
        user.access_token = sar.access_token
        user.refresh_token = sar.refresh_token
        user.expires_at = sar.expires_at
        user.last_login = datetime.now(UTC)
        user.name = sar.make_username()
        await db_session.refresh(user)
    else:
        user = User(
            id=user_id,
            access_token=sar.access_token,
            refresh_token=sar.refresh_token,
            expires_at=sar.expires_at,
            name=sar.make_username(),
        )
        db_session.add(user)
        await db_session.commit()

    expiration = timedelta(days=30) if data.remember_longer else timedelta(days=1)
    token = jwt_auth.create_token(identifier=str(user_id), token_expiration=expiration)
    return AuthResponse(token=token, user=MinimalUser(id=user_id))
