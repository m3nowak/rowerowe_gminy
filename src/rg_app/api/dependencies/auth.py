from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.exceptions import HTTPException

from rg_app.api.dependencies.config import Config


@dataclass
class UserInfo:
    user_id: int
    username: str


def _provide_user(request: Request, config: Config) -> UserInfo | None:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    token = auth.split(" ")[1]
    try:
        decoded = jwt.decode(token, config.auth.get_secret(), algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return UserInfo(user_id=int(decoded["sub"]), username=decoded["preferred_username"])


def _provide_user_force(request: Request, config: Config) -> UserInfo:
    user = _provide_user(request, config)
    if user is None:
        raise HTTPException(status_code=401, detail="Missing token")
    return user


UserInfoOptional = Annotated[UserInfo | None, Depends(_provide_user)]
UserInfoRequired = Annotated[UserInfo, Depends(_provide_user_force)]
