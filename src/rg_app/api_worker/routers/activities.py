from datetime import datetime

import fastapi

from rg_app.api_worker.dependencies.auth import UserInfoRequired
from rg_app.api_worker.dependencies.broker import NatsBroker
from rg_app.common.msg.base_model import BaseModel
from rg_app.common.msg.cmd import BacklogActivityCmd
from rg_app.nats_defs.local import STREAM_ACTIVITY_CMD

router = fastapi.APIRouter(tags=["activities"], prefix="/activities")


class BacklogRequest(BaseModel):
    period_from: datetime
    period_to: datetime


@router.post("/backlog")
async def backlog(backlog_request: BacklogRequest, user_info: UserInfoRequired, broker: NatsBroker):
    msg = BacklogActivityCmd(
        owner_id=user_info.user_id,
        period_from=backlog_request.period_from,
        period_to=backlog_request.period_to,
        type="backlog",
    )
    await broker.publish(msg, f"rg.internal.cmd.activity.backlog.{user_info.user_id}", stream=STREAM_ACTIVITY_CMD.name)
