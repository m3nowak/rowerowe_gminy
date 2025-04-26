import typing as ty
from logging import Logger

from faststream import Depends
from faststream.nats import NatsRouter
from faststream.nats.annotations import NatsBroker
from httpx import HTTPStatusError
from sqlalchemy import text

from rg_app.common.faststream.otel import otel_logger
from rg_app.common.internal.common import BasicResponse
from rg_app.common.internal.user_svc import AccountDeleteRequest, UnlockedRequest
from rg_app.common.strava.user import deauthorize
from rg_app.db.models.models import User
from rg_app.nats_defs.local import STREAM_ACTIVITY_CMD
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.dependencies.db import AsyncSessionDI
from rg_app.worker.dependencies.http_client import AsyncClientDI
from rg_app.worker.dependencies.strava import RateLimitManagerDI, StravaTokenManagerDI

user_svc_router = NatsRouter("rg.svc.user.")


@user_svc_router.subscriber("regions-unlocked", DEFAULT_QUEUE)
async def user_unlocked(
    body: UnlockedRequest,
    session: AsyncSessionDI,
) -> list[str]:
    query = text(
        """
        SELECT 
        JSONB_AGG(DISTINCT element) as unique_regions
        FROM activity,
        JSONB_ARRAY_ELEMENTS(visited_regions) as element
        where user_id = :uid;
        """
    )
    result = await session.execute(query, {"uid": body.user_id})
    return result.scalar_one()


@user_svc_router.subscriber("delete-account", DEFAULT_QUEUE)
async def delete_account(
    body: AccountDeleteRequest,
    broker: NatsBroker,
    http_client: AsyncClientDI,
    rlm: RateLimitManagerDI,
    stm: StravaTokenManagerDI,
    session: AsyncSessionDI,
    logger: Logger = Depends(otel_logger),
) -> BasicResponse:
    user_id = body.user_id
    nats_conn = broker._connection

    try:
        token = await stm.get_token(user_id)
        await deauthorize(client=http_client, rlm=rlm, access_token=token)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            pass
        else:
            return "ERROR"

    assert nats_conn is not None
    js = nats_conn.jetstream()
    activity_stream_name = ty.cast(str, STREAM_ACTIVITY_CMD.name)
    await js.purge_stream(activity_stream_name, subject=f"rg.internal.cmd.activity.*.{user_id}.>")
    user = await session.get(User, user_id)
    if user:
        await session.delete(user)
    await session.commit()

    logger.warning(f"User {user_id} deleted")

    return "OK"
