import fastapi

from rg_app.api.common import user_check_last_trigger
from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.models.athletes import AthleteDetail
from rg_app.db.models import User

router = fastapi.APIRouter(tags=["athletes"], prefix="/athletes")


@router.get("/me")
async def get_logged_in_user(
    user_info: UserInfoRequired,
    session: AsyncSession,
) -> AthleteDetail:
    user_id = user_info.user_id
    # await asyncio.sleep(1)
    # raise fastapi.HTTPException(status_code=500, detail="Internal server error, user not found")
    # auth = await stm.get_httpx_auth(user_id)
    user = await session.get(User, user_id)
    assert user is not None
    return AthleteDetail(
        id=user_id,
        created_at=user.strava_account_created_at,
        last_backlog_sync=user.last_backlog_sync,
        backlog_sync_eligible=user_check_last_trigger(user),
        strava_account_created_at=user.strava_account_created_at,
    )
