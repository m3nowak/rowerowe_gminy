from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.exceptions import HTTPException

from rg_app.api.common import AUTH_COOKIE_NAME
from rg_app.api.dependencies.config import Config


@dataclass
class UserInfo:
    user_id: int
    username: str


def _provide_claims(request: Request, config: Config) -> dict[str, Any] | None:
    auth_cookie = request.cookies.get(AUTH_COOKIE_NAME)
    token = None
    if auth_cookie:
        token = auth_cookie
    else:
        auth = request.headers.get("Authorization")
        if auth:
            token = auth.split(" ")[1]
    if not token:
        return None
    try:
        decoded = jwt.decode(token, config.auth.get_secret(), algorithms=["HS256"])
        return decoded
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


UserClaims = Annotated[dict[str, Any] | None, Depends(_provide_claims)]


def _provide_user(claims: UserClaims) -> UserInfo | None:
    if not claims:
        return None
    return UserInfo(user_id=int(claims["sub"]), username=claims["preferred_username"])


UserInfoOptional = Annotated[UserInfo | None, Depends(_provide_user)]


def _provide_user_force(user: UserInfoOptional) -> UserInfo:
    if user is None:
        raise HTTPException(status_code=401, detail="Missing token")
    return user


UserInfoRequired = Annotated[UserInfo, Depends(_provide_user_force)]
