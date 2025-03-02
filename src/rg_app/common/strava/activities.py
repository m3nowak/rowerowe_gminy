from datetime import UTC, datetime
from typing import Sequence

from httpx import AsyncClient
from pydantic import TypeAdapter

from .auth import StravaAuth
from .helpers import MAX_PAGE_SIZE
from .models.activity import ActivityPartial, ActivityStreamSet
from .models.base import PaginatedResult
from .rate_limits import RateLimitManager

_activity_list_adapter = TypeAdapter(Sequence[ActivityPartial])


async def get_activity_range(
    client: AsyncClient,
    period_from: datetime,
    period_to: datetime,
    page: int,
    auth: StravaAuth,
    rlm: RateLimitManager,
) -> PaginatedResult[ActivityPartial]:
    """
    Get activities for a given period
    page: 0-based
    """
    query = {
        "before": int(period_to.timestamp()),
        "after": int(period_from.timestamp()),
        "page": page + 1,
        "per_page": MAX_PAGE_SIZE,
    }
    resp = await client.get("https://www.strava.com/api/v3/athlete/activities", params=query, auth=auth)
    resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
    activity_list = _activity_list_adapter.validate_json(resp.text)
    return PaginatedResult(items=activity_list, page=page, has_more=len(activity_list) != 0)


async def get_activity(
    client: AsyncClient,
    activity_id: int,
    auth: StravaAuth,
    rlm: RateLimitManager,
) -> ActivityPartial:
    resp = await client.get(f"https://www.strava.com/api/v3/activities/{activity_id}", auth=auth)
    resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
    return ActivityPartial.model_validate_json(resp.text)


async def verify_activities_accessible(
    client: AsyncClient,
    auth: StravaAuth,
    rlm: RateLimitManager,
) -> bool:
    """
    Check current user can have its activities accessed
    """
    query = {
        "before": int(datetime.now(UTC).timestamp()),
        "page": 1,
        "per_page": MAX_PAGE_SIZE,
    }
    resp = await client.get("https://www.strava.com/api/v3/athlete/activities", params=query, auth=auth)
    if resp.status_code == 401:
        return False
    resp.raise_for_status()
    return True


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
