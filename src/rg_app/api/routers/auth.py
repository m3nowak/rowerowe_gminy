from datetime import UTC, datetime, timedelta

import fastapi
import jwt
from httpx import HTTPStatusError

from rg_app.api.dependencies.config import Config
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.dependencies.debug_flag import DebugFlag
from rg_app.api.dependencies.http_client import AsyncClient
from rg_app.api.dependencies.strava import RateLimitManager, StravaTokenManager
from rg_app.api.models.auth import LoginRequest, LoginResponse
from rg_app.common.strava.athletes import get_athlete
from rg_app.common.strava.auth import StravaAuth
from rg_app.db import User

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
async def login(
    login_data: LoginRequest,
    config: Config,
    stm: StravaTokenManager,
    session: AsyncSession,
    df: DebugFlag,
    async_client: AsyncClient,
    rlm: RateLimitManager,
) -> LoginResponse:
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

    # User is legit

    user = await session.get(User, atr.athlete.id)
    is_first_login = user is None
    if user:
        user.access_token = atr.access_token
        user.refresh_token = atr.refresh_token
        user.expires_at = atr.expires_at
        user.last_login = datetime.now(UTC)
        user.name = atr.friendly_name()
    else:
        auth = StravaAuth(atr.access_token)
        athlete_raw = await get_athlete(async_client, auth, rlm)
        user = User(
            id=atr.athlete.id,
            access_token=atr.access_token,
            refresh_token=atr.refresh_token,
            expires_at=atr.expires_at,
            last_login=datetime.now(UTC),
            name=atr.friendly_name(),
            strava_account_created_at=athlete_raw.created_at,
        )
        session.add(user)
    await session.commit()

    expiry = (
        timedelta(hours=config.auth.long_expiry_hours)
        if login_data.remember_longer
        else timedelta(hours=config.auth.standard_expiry_hours)
    )

    token = create_token(str(atr.athlete.id), expiry, config.auth.get_secret(), atr.friendly_name())
    return LoginResponse(access_token=token, token_type="bearer", is_first_login=is_first_login or df)
