"""
Delay messages if rate limits are close to being reached
"""

from faststream import Depends
from faststream.exceptions import NackMessage

from rg_app.worker.dependencies.strava import RateLimitManagerDI


def rate_limit_percent_below(percent: float):
    async def rl_dep(
        rate_limit_manager: RateLimitManagerDI,
    ):
        limits_set = await rate_limit_manager.get_limits()
        if limits_set is not None:
            if limits_set.current_read_percent >= percent:
                raise NackMessage(delay=120)

    return Depends(rl_dep)
