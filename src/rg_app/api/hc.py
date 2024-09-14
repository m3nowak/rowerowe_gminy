from litestar import get

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import ServiceUnavailableException

@get("/hc")
async def hc_handler(db_session: AsyncSession) -> str:
    """Health check handler"""
    try:
        resp = await db_session.execute(sa.text("SELECT 1"))
        return f"Server ready, {resp.scalar()}"
    except Exception:
        raise ServiceUnavailableException("DB connection is not ready")
