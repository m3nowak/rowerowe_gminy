import asyncio
from datetime import datetime, timedelta
from typing import Literal

import fastapi

from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.http_client import AsyncClient
from rg_app.api.dependencies.strava import RateLimitManager, StravaTokenManager
from rg_app.api.models.athlete import AthleteDetail
from rg_app.common.msg.base_model import BaseModel
from rg_app.common.msg.cmd import BacklogActivityCmd
from rg_app.common.strava.athlete import get_athlete
from rg_app.nats_defs.local import STREAM_ACTIVITY_CMD

router = fastapi.APIRouter(tags=["athlete"], prefix="/athlete")


@router.get("")
async def get_logged_in_user(
    user_info: UserInfoRequired,
    stm: StravaTokenManager,
    rlm: RateLimitManager,
    async_client: AsyncClient,
) -> AthleteDetail:
    user_id = user_info.user_id
    auth = await stm.get_httpx_auth(user_id)
    athlete_raw = await get_athlete(async_client, auth, rlm)
    return AthleteDetail(id=athlete_raw.id, created_at=athlete_raw.created_at)


class BacklogRequest(BaseModel):
    period_from: datetime
    period_to: datetime


@router.post("/backlog")
async def backlog(backlog_request: BacklogRequest, user_info: UserInfoRequired, broker: NatsBroker) -> Literal["OK"]:
    period_from = backlog_request.period_from
    period_to = period_from + timedelta(days=30)
    should_continue = True
    awaitables = []
    while should_continue:
        msg = BacklogActivityCmd(
            owner_id=user_info.user_id,
            period_from=period_from,
            period_to=min(period_to, backlog_request.period_to),
            type="backlog",
        )
        awaitables.append(
            broker.publish(
                msg, f"rg.internal.cmd.activity.backlog.{user_info.user_id}", stream=STREAM_ACTIVITY_CMD.name
            )
        )
        if period_to > backlog_request.period_to:
            should_continue = False
        else:
            period_from = period_to
            period_to += timedelta(days=30)
    await asyncio.gather(*awaitables)
    return "OK"
