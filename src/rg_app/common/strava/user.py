from httpx import AsyncClient

from .rate_limits import RateLimitManager


async def deauthorize(
    client: AsyncClient,
    rlm: RateLimitManager,
    access_token: str,
):
    """
    Deauthorize athlete
    """
    resp = await client.post("https://www.strava.com/oauth/deauthorize", params={"access_token": access_token})
    if resp.status_code != 401:
        resp.raise_for_status()
    await rlm.feed_headers(resp.headers)
