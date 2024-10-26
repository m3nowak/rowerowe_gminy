from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, AsyncGenerator, Literal, Self

import httpx
import msgspec

_URL = "https://www.strava.com/oauth/token"


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


class StravaTokenManager:
    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = None

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[Self, None]:
        async with httpx.AsyncClient() as client:
            self._client = client
            try:
                yield self
            finally:
                pass

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
        data = resp.json()
        return TokenResponse(
            access_token=data["access_token"],
            expires_at=datetime.fromtimestamp(data["expires_at"], UTC),
            refresh_token=data["refresh_token"],
        )

    async def authenticate(self, code: str) -> AthleteTokenResponse:
        assert self._client is not None, "You must call this in async with begin() block"
        request = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        resp = await self._client.post(_URL, data=request)
        resp.raise_for_status()
        data = resp.json()
        return AthleteTokenResponse(
            access_token=data["access_token"],
            expires_at=datetime.fromtimestamp(data["expires_at"]),
            refresh_token=data["refresh_token"],
            athlete=data["athlete"],
        )
