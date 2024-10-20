import typing as ty
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from litestar import Response, post
from litestar.security.jwt import OAuth2Login
from litestar.status_codes import HTTP_200_OK
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.msg import BaseStruct
from rg_app.common.strava import AthleteTokenResponse, StravaTokenManager
from rg_app.db import User

from .jwt import CreateTokenHandler


def make_username(atr: AthleteTokenResponse) -> str:
    if atr.athlete.get("firstname") is not None or atr.athlete.get("lastname") is not None:
        snc = [atr.athlete.get("firstname"), atr.athlete.get("lastname")]
        snc = list(filter(lambda x: x is not None, snc))
        return " ".join(snc)  # type: ignore
    elif atr.athlete.get("username") is not None:
        return atr.athlete["username"]
    else:
        return str(atr.athlete["id"])


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


@post(
    "/authenticate/login",
    tags=["auth"],
    description="Authenticate with Strava with provided code",
    status_code=HTTP_200_OK,
)
async def authenticate_handler(
    data: AuthRequest,
    db_session: AsyncSession,
    o2a: CreateTokenHandler,
    strava_token_mgr: StravaTokenManager,
) -> Response[OAuth2Login]:
    atr = await strava_token_mgr.authenticate(data.code)
    assert atr is not None
    user_id: int | None = atr.athlete.get("id")
    assert user_id is not None

    user = await db_session.get(User, user_id)
    if user:
        user.access_token = atr.access_token
        user.refresh_token = atr.refresh_token
        user.expires_at = atr.expires_at
        user.last_login = datetime.now(UTC)
        user.name = make_username(atr)
        await db_session.refresh(user)
    else:
        user = User(
            id=user_id,
            access_token=atr.access_token,
            refresh_token=atr.refresh_token,
            expires_at=atr.expires_at,
            name=make_username(atr),
        )
        db_session.add(user)
        await db_session.commit()

    extras = {"username": user.name, "scopes": data.scopes}

    expiration = timedelta(days=30) if data.remember_longer else timedelta(days=1)
    resp = o2a.create_response(identifier=str(user_id), token_expiration=expiration, token_extras=extras)
    return resp
