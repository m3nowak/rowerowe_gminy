import fastapi
import sqlalchemy as sa

from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.db import AsyncSession

router = fastapi.APIRouter(tags=["health"])


@router.get("/health")
async def health(session: AsyncSession, broker: NatsBroker):
    db_res = session.execute(sa.text("SELECT 1"))
    br_res = broker.ping(15)
    assert (await db_res).scalar_one() == 1
    assert await br_res
    return {"status": "ok"}
