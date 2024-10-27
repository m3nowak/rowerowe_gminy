import sqlalchemy as sa
from litestar import get
from litestar.exceptions import ServiceUnavailableException
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.strava import RateLimitManager, RateLimitSet


@get("/hc", tags=["internals"], raises=[ServiceUnavailableException])
async def hc_handler(db_session: AsyncSession) -> str:
    """Health check handler"""
    try:
        resp = await db_session.execute(sa.text("SELECT 1"))
        return f"Server ready, {resp.scalar()}"
    except Exception:
        raise ServiceUnavailableException("DB connection is not ready")


@get("/rate-limits", tags=["internals"])
async def rate_limits_handler(rate_limits: RateLimitManager) -> RateLimitSet | None:
    """Strava rate limits handler"""
    return await rate_limits.get_limits()
