from httpx import AsyncClient

from .auth import StravaAuth
from .models.athlete import AthletePartial
from .rate_limits import RateLimitManager


async def get_athlete(
    client: AsyncClient,
    auth: StravaAuth,
    rlm: RateLimitManager,
) -> AthletePartial:
    """
    Get athlete info
    """
    resp = await client.get("https://www.strava.com/api/v3/athlete", auth=auth)
    resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
    return AthletePartial.model_validate_json(resp.text)
