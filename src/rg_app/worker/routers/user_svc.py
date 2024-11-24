from faststream import Depends
from faststream.nats import NatsRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.internal.user_svc import UnlockedRequest
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.deps import db_session

user_svc_router = NatsRouter("rg.svc.user.")


@user_svc_router.subscriber("regions-unlocked", DEFAULT_QUEUE)
async def user_unlocked(
    body: UnlockedRequest,
    session: AsyncSession = Depends(db_session),
) -> list[str]:
    query = text(
        """
        SELECT 
        JSONB_AGG(DISTINCT element) as unique_regions
        FROM activity,
        JSONB_ARRAY_ELEMENTS(visited_regions) as element
        where user_id = :uid;
        """
    )
    result = await session.execute(query, {"uid": body.user_id})
    return result.scalar_one()
