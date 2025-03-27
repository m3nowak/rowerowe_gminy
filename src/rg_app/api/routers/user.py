import fastapi

from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.db import AsyncSession
from rg_app.common.internal.common import BasicResponse
from rg_app.common.internal.user_svc import AccountDeleteRequest
from rg_app.db.models import User

router = fastapi.APIRouter(tags=["user"], prefix="/user")


@router.delete("")
async def delete_account(
    session: AsyncSession,
    broker: NatsBroker,
    user_info: UserInfoRequired,
) -> BasicResponse:
    user_id = user_info.user_id
    user = await session.get(User, user_id)
    if user is None:
        raise fastapi.HTTPException(status_code=404, detail="User not found")
    resp = await broker.request(
        AccountDeleteRequest(user_id=user_id),
        "rg.svc.user.delete-account",
    )
    resp_dec = resp.body.decode()
    if resp_dec != "OK":
        raise fastapi.HTTPException(status_code=500, detail="Internal server error")
    return resp_dec
