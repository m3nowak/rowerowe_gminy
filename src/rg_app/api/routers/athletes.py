import fastapi

from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.http_client import AsyncClient
from rg_app.api.dependencies.strava import RateLimitManager, StravaTokenManager
from rg_app.api.models.athletes import AthleteDetail
from rg_app.common.strava.athletes import get_athlete

router = fastapi.APIRouter(tags=["athletes"], prefix="/athletes")


@router.get("/me")
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
