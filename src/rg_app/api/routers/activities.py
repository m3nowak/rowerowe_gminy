import asyncio
from datetime import UTC, datetime, timedelta
from typing import Literal

import fastapi

from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.dependencies.debug_flag import DebugFlag
from rg_app.common.msg.base_model import BaseModel
from rg_app.common.msg.cmd import BacklogActivityCmd
from rg_app.db.models import User
from rg_app.nats_defs.local import STREAM_ACTIVITY_CMD

router = fastapi.APIRouter(tags=["activities"], prefix="/activities")

BACKLOG_TRIGGER_TIMEOUT = timedelta(days=14)


class BacklogRequest(BaseModel):
    period_from: datetime
    period_to: datetime


class BacklogLastTriggerResponse(BaseModel):
    last_trigger: datetime | None
    eligible: bool


def _check_last_trigger(user: User) -> bool:
    """
    Check if the user is eligible for backlog trigger
    """
    return user.last_backlog_sync is None or user.last_backlog_sync + BACKLOG_TRIGGER_TIMEOUT < datetime.now(UTC)


@router.post("/backlog")
async def backlog(
    backlog_request: BacklogRequest,
    user_info: UserInfoRequired,
    broker: NatsBroker,
    session: AsyncSession,
    debug: DebugFlag,
) -> Literal["OK"]:
    period_from = backlog_request.period_from
    period_to = period_from + timedelta(days=30)
    should_continue = True
    awaitables = []
    user = await session.get(User, user_info.user_id)
    if user is None:
        raise fastapi.HTTPException(status_code=500, detail="Internal server error, user not found")
    if not _check_last_trigger(user) and not debug:
        raise fastapi.HTTPException(status_code=400, detail="Backlog trigger not allowed")
    user.last_backlog_sync = datetime.now(UTC)
    await session.commit()
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


@router.get("/backlog/last-trigger")
async def backlog_last_trigger(user_info: UserInfoRequired, session: AsyncSession) -> BacklogLastTriggerResponse:
    user = await session.get(User, user_info.user_id)
    if user is None:
        raise fastapi.HTTPException(status_code=500, detail="Internal server error, user not found")
    return BacklogLastTriggerResponse(
        last_trigger=user.last_backlog_sync,
        eligible=_check_last_trigger(user),
    )
