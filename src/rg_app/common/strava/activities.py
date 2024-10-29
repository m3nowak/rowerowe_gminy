from httpx import AsyncClient

from .auth import StravaAuth
from .models.activity import ActivityPartial, ActivityStreamSet
from .rate_limits import RateLimitManager


async def get_activity(
    client: AsyncClient, activity_id: int, auth: StravaAuth, rlm: RateLimitManager
) -> ActivityPartial:
    resp = await client.get(f"https://www.strava.com/api/v3/activities/{activity_id}", auth=auth)
    resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
    return ActivityPartial.model_validate_json(resp.text)


async def get_activity_streams(
    client: AsyncClient, activity_id: int, auth: StravaAuth, rlm: RateLimitManager
) -> ActivityStreamSet:
    streams = ["time", "latlng", "altitude", "distance"]
    resp = await client.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
        params={"keys": ",".join(streams), "key_by_type": "true"},
        auth=auth,
    )
    resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
    return ActivityStreamSet.model_validate_json(resp.text)
