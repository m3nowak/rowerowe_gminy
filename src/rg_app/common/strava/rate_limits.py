import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import AsyncGenerator, Self

import msgspec.json
import nats.js.errors
from httpx import Headers
from nats.aio.client import Client as NATS

from rg_app.common.msg.base_struct import BaseStruct


class RateLimit(BaseStruct):
    usage: int
    limit: int

    @property
    def remaining(self):
        return self.limit - self.usage

    @property
    def use_percent(self):
        return self.usage / self.limit


class RateLimitSet(BaseStruct):
    read_15m: RateLimit
    read_daily: RateLimit
    any_15m: RateLimit
    any_daily: RateLimit

    updated_at: datetime

    def _has_15m_mark_passed(self):
        now = datetime.now(UTC)
        then = self.updated_at
        conditions = [
            now.year != then.year,
            now.month != then.month,
            now.day != then.day,
            now.hour != then.hour,
            now.minute // 15 != then.minute // 15,
        ]
        return any(conditions)

    def _has_daily_mark_passed(self):
        now = datetime.now(UTC)
        then = self.updated_at
        conditions = [now.year != then.year, now.month != then.month, now.day != then.day]
        return any(conditions)

    @property
    def current_read_percent(self):
        if self._has_daily_mark_passed():
            return 0.0
        elif self._has_15m_mark_passed():
            return self.read_daily.use_percent
        else:
            return max(self.read_15m.use_percent, self.read_daily.use_percent)

    @property
    def current_any_percent(self):
        if self._has_daily_mark_passed():
            return 0.0
        elif self._has_15m_mark_passed():
            return self.any_daily.use_percent
        else:
            return max(self.any_15m.use_percent, self.any_daily.use_percent)

    @property
    def current_all_percent(self):
        return max(self.current_read_percent, self.current_any_percent)


def extract_limits(headers: Headers) -> RateLimitSet | None:
    date = headers.get("Date")
    if date is None:
        date = datetime.now(UTC)
    else:
        # format: Tue, 10 Oct 2020 20:11:05 GMT
        date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
        date = date.replace(tzinfo=UTC)
    try:
        al15, ald = headers.get("X-RateLimit-Limit").strip().split(",")
        au15, aud = headers.get("X-RateLimit-Usage").strip().split(",")
        rl15, rld = headers.get("X-ReadRateLimit-Limit").strip().split(",")
        ru15, rud = headers.get("X-ReadRateLimit-Usage").strip().split(",")
        return RateLimitSet(
            read_15m=RateLimit(usage=int(ru15), limit=int(rl15)),
            read_daily=RateLimit(usage=int(rud), limit=int(rld)),
            any_15m=RateLimit(usage=int(au15), limit=int(al15)),
            any_daily=RateLimit(usage=int(aud), limit=int(ald)),
            updated_at=date,
        )
    except Exception:
        return None


@dataclass
class RLNatsConfig:
    nats_conn: NATS
    kv_name: str = "rate-limits"
    js_domain: str | None = None


class RateLimitManager:
    def __init__(self, rl_nats_config: RLNatsConfig | None = None):
        if rl_nats_config is not None:
            self._nc = rl_nats_config.nats_conn
            self._kv_name = rl_nats_config.kv_name
            self._js_domain = rl_nats_config.js_domain
        else:
            self._nc = None
            self._kv_name = None
            self._js_domain = None
        self._js = None
        self._kv = None
        self.limits_set = ContextVar[RateLimitSet | None]("limits_set", default=None)
        self._refresh_task = None

    async def refresh_task(self):
        assert self._kv is not None
        assert self._kv_name is not None
        while True:
            await asyncio.sleep(60)
            try:
                limits_raw = await self._kv.get(self._kv_name)
                if limits_raw.value is not None:
                    self.limits_set.set(msgspec.json.decode(limits_raw.value, type=RateLimitSet))
            except nats.js.errors.KeyNotFoundError:
                pass

    @asynccontextmanager
    async def begin(self) -> AsyncGenerator[Self, None]:
        if self._nc is not None:
            self._js = self._nc.jetstream(domain=self._js_domain)
            assert self._kv_name is not None
            self._kv = await self._js.key_value(self._kv_name)
            try:
                limits_raw = await self._kv.get(self._kv_name)
                if limits_raw.value is not None:
                    self.limits_set.set(msgspec.json.decode(limits_raw.value, type=RateLimitSet))
            except nats.js.errors.KeyNotFoundError:
                pass

            self._refresh_task = asyncio.create_task(self.refresh_task())

            self._sub = await self._kv.watch(self._kv_name)
            try:
                yield self
            finally:
                if self._refresh_task is not None:
                    self._refresh_task.cancel()
                self._refresh_task = None
                self._kv = None
                self._js = None

    @property
    def _nc_available(self):
        return self._nc is not None

    async def get_limits(self) -> RateLimitSet | None:
        return self.limits_set.get()

    async def feed_headers(self, headers: Headers):
        limits = extract_limits(headers)
        if limits is not None:
            if self._kv is not None:
                assert self._kv_name is not None
                await self._kv.put(self._kv_name, msgspec.json.encode(limits))
            self.limits_set.set(limits)
