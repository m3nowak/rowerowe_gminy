import fastapi

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
    # auth = await stm.get_httpx_auth(user_id)
    user = await session.get(User, user_id)
    assert user is not None
    return AthleteDetail(id=user_id, created_at=user.strava_account_created_at)
