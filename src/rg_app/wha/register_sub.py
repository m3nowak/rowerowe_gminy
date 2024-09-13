import asyncio
from urllib.parse import urljoin

import httpx

from .common import LOCAL_WH_URL
from .config import Config

STRAVA_SUB_URL = "https://www.strava.com/api/v3/push_subscriptions"


async def register_sub(config: Config, sleep: int = 5):
    await asyncio.sleep(sleep)
    async with httpx.AsyncClient() as client:
        current_subs = await client.get(
            STRAVA_SUB_URL, params={"client_id": config.strava_client_id, "client_secret": config.strava_client_secret}
        )
        current_subs.raise_for_status()
        sub_list = current_subs.json()
        if sub_list:
            for sub in sub_list:
                sub_id = sub["id"]
                await client.delete(urljoin(STRAVA_SUB_URL, str(sub_id)))
        sub = {
            "client_id": config.strava_client_id,
            "client_secret": config.strava_client_secret,
            "callback_url": urljoin(config.self_url, LOCAL_WH_URL),
            "verify_token": config.verify_token,
        }
        new_sub = await client.post(STRAVA_SUB_URL, data=sub)
        new_sub.raise_for_status()
