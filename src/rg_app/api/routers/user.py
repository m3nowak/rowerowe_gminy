import fastapi

from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.broker import NatsBroker
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.models.user import UserSettings, UserSettingsPartial
from rg_app.common.enums import DescUpdateOptions
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


@router.get("/settings")
async def get_user_settings(
    session: AsyncSession,
    user_info: UserInfoRequired,
) -> UserSettings:
    user_id = user_info.user_id
    user = await session.get(User, user_id)
    if user is None:
        raise fastapi.HTTPException(status_code=404, detail="User not found")
    return UserSettings(update_strava_desc=DescUpdateOptions(user.update_strava_desc))


@router.patch("/settings")
async def update_user_settings(
    session: AsyncSession,
    user_info: UserInfoRequired,
    update_patch: UserSettingsPartial,
) -> BasicResponse:
    user_id = user_info.user_id
    user = await session.get(User, user_id)
    if user is None:
        raise fastapi.HTTPException(status_code=404, detail="User not found")

    if update_patch.update_strava_desc is not None:
        user.update_strava_desc = update_patch.update_strava_desc

    await session.commit()
    return "OK"
