import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator, Literal, Self

import httpx
import msgspec
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.db import User

_URL = "https://www.strava.com/oauth/token"

_TRIES = 3


class StravaAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


class StravaAuthResponse(msgspec.Struct):
    token_type: Literal["Bearer"]
    expires_at: int
    expires_in: int
    refresh_token: str
    access_token: str
    athlete: dict[str, Any]


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    expires_at: datetime
    refresh_token: str


@dataclass(frozen=True)
class AthleteTokenResponse(TokenResponse):
    athlete: dict[str, Any]


class StravaTokenResponseAthlete(BaseModel):
    id: int
    username: str | None
    firstname: str | None
    lastname: str | None


class StravaTokenResponse(BaseModel):
    access_token: str
    expires_at: datetime
    refresh_token: str
    athlete: StravaTokenResponseAthlete

    def friendly_name(self) -> str:
        """
        Returns a friendly name for the athlete.
        First name, last name, or username if available.
        As a last resort, the athlete's ID.
        """
        if self.athlete.firstname or self.athlete.lastname:
            snc = [self.athlete.firstname, self.athlete.lastname]
            snc = list(filter(lambda x: x is not None, snc))
            return " ".join(snc)  # type: ignore
        elif self.athlete.username:
            return self.athlete.username
        else:
            return str(self.athlete.id)


class StravaTokenManager:
    def __init__(
        self, client_id: str, client_secret: str, rate_limit_mgr: RateLimitManager, async_engine: AsyncEngine
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = None
        self._rate_limit_mgr = rate_limit_mgr
        self._async_engine = async_engine
        self._sa_sm = async_sessionmaker(self._async_engine, expire_on_commit=False)

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[Self, None]:
        async with httpx.AsyncClient() as client:
            self._client = client
            try:
                yield self
            finally:
                pass

    async def get_token(self, athlete_id: int) -> str:
        assert self._client is not None, "You must call this in async with begin() block"
        async with self._sa_sm() as session:
            result = await session.execute(sa.select(User).filter(User.id == athlete_id))
            user = result.scalars().one_or_none()
            if user is None:
                raise ValueError(f"User with id {athlete_id} not found")
            now = datetime.now(UTC)
            if user.access_token is None or user.expires_at < now + timedelta(minutes=5):
                new_token = await self.refresh(user.refresh_token)
                user.access_token = new_token.access_token
                user.expires_at = new_token.expires_at
                await session.commit()
            return user.access_token

    async def get_httpx_auth(self, athlete_id: int) -> StravaAuth:
        token = await self.get_token(athlete_id)
        return StravaAuth(token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        assert self._client is not None, "You must call this in async with begin() block"
        request = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = await self._client.post(_URL, data=request)
        resp.raise_for_status()
        await self._rate_limit_mgr.feed_headers(resp.headers)
        data = resp.json()
        return TokenResponse(
            access_token=data["access_token"],
            expires_at=datetime.fromtimestamp(data["expires_at"], UTC),
            refresh_token=data["refresh_token"],
        )

    async def authenticate(self, code: str) -> StravaTokenResponse:
        assert self._client is not None, "You must call this in async with begin() block"
        request = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        for i in range(_TRIES):
            resp = await self._client.post(_URL, data=request)
            if resp.is_success:
                return StravaTokenResponse.model_validate_json(resp.text)
            await self._rate_limit_mgr.feed_headers(resp.headers)
            if i < _TRIES - 1:
                await asyncio.sleep(1)
            else:
                resp.raise_for_status()
                raise ValueError("Unreachable")
        raise ValueError("Unreachable")
