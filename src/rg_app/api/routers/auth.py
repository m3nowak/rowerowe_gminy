import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import fastapi
import jwt
from fastapi import Query
from httpx import HTTPStatusError

from rg_app.api.common import AUTH_COOKIE_NAME
from rg_app.api.dependencies.auth import UserClaims
from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.config import Config
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.dependencies.debug_flag import DebugFlag
from rg_app.api.dependencies.http_client import AsyncClient
from rg_app.api.dependencies.strava import RateLimitManager, StravaTokenManager
from rg_app.api.models.auth import (
    LoginErrorCause,
    LoginRequest,
    LoginResponse,
    LoginResponseCookie,
    LoginResponseError,
    StravaScopes,
)
from rg_app.common.msg.cmd import BacklogActivityCmd
from rg_app.common.strava.activities import verify_activities_accessible
from rg_app.common.strava.athletes import get_athlete
from rg_app.common.strava.auth import StravaAuth
from rg_app.db import User
from rg_app.nats_defs.local import STREAM_ACTIVITY_CMD

router = fastapi.APIRouter(tags=["auth"])


def create_token(user_id: str, expiry: timedelta, secret: str, username: str) -> tuple[str, dict[str, Any]]:
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + expiry,
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC) - timedelta(seconds=1),
        "preferred_username": username,
    }
    return jwt.encode(payload, secret, algorithm="HS256"), payload


_PERIOD_STEP = timedelta(days=365)


async def _initialize_backlog_import(
    user: User,
    broker: NatsBroker,
):
    now = datetime.now(UTC)
    period_from = user.strava_account_created_at
    period_to = period_from + _PERIOD_STEP
    should_continue = True
    awaitables = []

    print(f"Backlog import for {user.id} from {period_from} to {now}")

    while should_continue:
        msg = BacklogActivityCmd(
            owner_id=user.id,
            period_from=period_from,
            period_to=min(period_to, now),
            type="backlog",
        )
        awaitables.append(
            broker.publish(msg, f"rg.internal.cmd.activity.backlog.{user.id}", stream=STREAM_ACTIVITY_CMD.name)
        )
        if period_to >= now:
            break
        period_from = period_to
        period_to = period_from + _PERIOD_STEP
    await asyncio.gather(*awaitables)


@router.post(
    "/login",
    # response_model=LoginResponse,
    responses={400: {"model": LoginResponseError}, 200: {"model": LoginResponse}},
)
async def login(
    login_data: LoginRequest,
    # as_cookie: Annotated[bool, Query(default=False, alias="asCookie")],
    config: Config,
    stm: StravaTokenManager,
    session: AsyncSession,
    df: DebugFlag,
    async_client: AsyncClient,
    rlm: RateLimitManager,
    broker: NatsBroker,
    response: fastapi.Response,
    as_cookie: bool = Query(default=False, alias="asCookie"),
) -> LoginResponse | LoginResponseError | LoginResponseCookie:
    if StravaScopes.ACTIVITY_READ not in login_data.scopes:
        response.status_code = 400
        return LoginResponseError(cause=LoginErrorCause.INVALID_SCOPE)

    try:
        atr = await stm.authenticate(login_data.code)
    except HTTPStatusError as hse:
        status_code = hse.response.status_code
        response.status_code = 400
        if status_code >= 400 and status_code < 500:
            return LoginResponseError(cause=LoginErrorCause.INVALID_CODE)
        else:
            return LoginResponseError(cause=LoginErrorCause.STRAVA_ERROR)

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
        accessible = await verify_activities_accessible(async_client, auth, rlm)

        if not accessible:
            response.status_code = 400
            return LoginResponseError(cause=LoginErrorCause.INVALID_SCOPE)

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

    if is_first_login:
        await session.refresh(user, attribute_names=["id", "strava_account_created_at"])
        await _initialize_backlog_import(user, broker)

    expiry = (
        timedelta(hours=config.auth.long_expiry_hours)
        if login_data.remember_longer
        else timedelta(hours=config.auth.standard_expiry_hours)
    )

    token, claims = create_token(str(atr.athlete.id), expiry, config.auth.get_secret(), atr.friendly_name())
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=not df,
        secure=not df,
        expires=datetime.now(UTC) + expiry,
        samesite="none",
    )
    if as_cookie:
        return LoginResponseCookie(
            is_first_login=is_first_login or df,
            token_claims=claims,
        )
    else:
        return LoginResponse(access_token=token, token_type="bearer", is_first_login=is_first_login or df)


@router.post("/logout", status_code=204)
async def logout(
    response: fastapi.Response,
):
    """
    Logout the user, by removing the cookie
    """
    response.delete_cookie(key=AUTH_COOKIE_NAME)


@router.get("/login-details")
async def login_details(
    claims: UserClaims,
) -> LoginResponseCookie:
    """
    Get the login details of the user
    """
    if not claims:
        raise fastapi.HTTPException(status_code=401, detail="Missing token")
    return LoginResponseCookie(is_first_login=False, token_claims=claims)
