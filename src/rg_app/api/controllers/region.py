import sqlalchemy as sa
from litestar import Controller, get
from nats.aio.client import Client as NatsClient
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.api.jwt import MinimalUser
from rg_app.api.models.region import LastVisitResponse
from rg_app.common.internal.user_svc import UnlockedRequest
from rg_app.db.models.models import Activity

str_list_adapter = TypeAdapter(list[str])


class RegionController(Controller):
    path = "/region"
    tags = ["region"]

    @get("/unlocked")
    async def get_unlocked(
        self,
        nats: NatsClient,
        user: MinimalUser,
        user_id: int | None = None,
    ) -> list[str]:
        user_id = user_id or user.id
        req = UnlockedRequest(user_id=user_id)
        resp = await nats.request("rg.svc.user.regions-unlocked", payload=req.model_dump_json().encode())
        return str_list_adapter.validate_json(resp.data)

    @get("/{region_id: str}/last-visit")
    async def get_user_last_visit(
        self,
        region_id: str,
        db_session: AsyncSession,
        user: MinimalUser,
        user_id: int | None = None,
    ) -> LastVisitResponse:
        user_id = user_id or user.id
        query = (
            sa.select(Activity.start)
            .where(
                sa.and_(
                    Activity.user_id == user_id,
                    sa.or_(
                        Activity.visited_regions.has_key(region_id),
                        Activity.visited_regions_additional.has_key(region_id),
                    ),
                )
            )
            .limit(1)
            .order_by(sa.desc(Activity.start))
        )
        result = await db_session.execute(query)
        row = result.scalar_one_or_none()
        return LastVisitResponse(visit=row)
