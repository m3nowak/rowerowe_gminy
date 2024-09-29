from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator

import httpx

_URL = "https://www.strava.com/oauth/token"


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    expires_at: datetime
    refresh_token: str


class TokenRefresher:
    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = None

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator["TokenRefresher", None]:
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
            expires_at=data["expires_at"],
            refresh_token=data["refresh_token"],
        )
