from datetime import UTC, datetime, timedelta

import fastapi
import jwt
from httpx import HTTPStatusError

from rg_app.api_worker.dependencies.config import Config
from rg_app.api_worker.dependencies.strava import StravaTokenManager
from rg_app.api_worker.models.auth import LoginRequest, LoginResponse

router = fastapi.APIRouter(tags=["auth"])


def create_token(user_id: str, expiry: timedelta, secret: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + expiry,
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC) - timedelta(seconds=1),
        "preferred_username": username,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@router.post("/login")
async def login(login_data: LoginRequest, config: Config, stm: StravaTokenManager) -> LoginResponse:
    try:
        atr = await stm.authenticate(login_data.code)
    except HTTPStatusError as hse:
        status_code = hse.response.status_code
        if status_code >= 400 and status_code < 500:
            raise fastapi.HTTPException(status_code=hse.response.status_code, detail=hse.response.text)
        else:
            raise fastapi.HTTPException(
                status_code=500, detail="Internal server error, unable to authenticate in strava"
            )

    assert atr is not None

    expiry = (
        timedelta(hours=config.auth.long_expiry_hours)
        if login_data.remember_longer
        else timedelta(hours=config.auth.standard_expiry_hours)
    )

    token = create_token(str(atr.athlete.id), expiry, config.auth.get_secret(), atr.friendly_name())
    return LoginResponse(access_token=token, token_type="bearer")
