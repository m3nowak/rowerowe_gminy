from datetime import datetime

import fastapi
from sqlalchemy import cast, func, select
from sqlalchemy.dialects.postgresql import JSONB

from rg_app.api_worker.dependencies.auth import UserInfoRequired
from rg_app.api_worker.dependencies.db import AsyncSession
from rg_app.common.msg.base_model import BaseModel
from rg_app.db import Activity

router = fastapi.APIRouter(tags=["regions"], prefix="/regions")


class UnlockedRegion(BaseModel):
    region_id: str


class UnlockedRegionDetail(UnlockedRegion):
    last_visited: datetime
    first_visited: datetime


@router.get("/unlocked")
async def unlocked(session: AsyncSession, user_info: UserInfoRequired) -> list[UnlockedRegion]:
    """
    Get all the regions that the user has unlocked
    """

    element = func.jsonb_array_elements(Activity.visited_regions).alias("element")

    query = (
        select(
            element.column.label("element"),
        )
        .select_from(Activity, element)
        .where(Activity.user_id == user_info.user_id)
        .group_by(element.column)
    )

    result = await session.execute(query)

    return [UnlockedRegion(region_id=row.element) for row in result]


@router.get("/unlocked/{region_id}")
async def unlocked_detail(region_id: str, session: AsyncSession, user_info: UserInfoRequired) -> UnlockedRegionDetail:
    """
    Get the details of a specific region that the user has unlocked
    """

    query = select(
        func.min(Activity.start).label("first_visited"),
        func.max(Activity.start).label("last_visited"),
    ).where(
        Activity.user_id == user_info.user_id,
        Activity.visited_regions.contains(cast(region_id, JSONB)),
    )

    result = await session.execute(query)

    row = result.fetchone()

    if row is None:
        raise fastapi.HTTPException(status_code=404, detail="Region not unlocked")
    else:
        return UnlockedRegionDetail(region_id=region_id, last_visited=row.last_visited, first_visited=row.first_visited)
