import typing as ty

from faststream import Depends
from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.strava.models.webhook import WebhookAthlete
from rg_app.db.models.models import User
from rg_app.nats_defs.local import (
    CONSUMER_REVOCATIONS,
    NAME_INCOMING_WHA_MIRROR,
    STREAM_ACTIVITY_CMD,
)
from rg_app.worker.deps import db_session

router = NatsRouter()

wha_stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)


@router.subscriber(
    config=CONSUMER_REVOCATIONS,
    stream=wha_stream,
    durable=CONSUMER_REVOCATIONS.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
    title=f"{wha_stream.name}/{CONSUMER_REVOCATIONS.durable_name}",
)
async def revocations_handle(
    body: WebhookAthlete,
    broker: NatsBroker,
    nats_msg: NatsMessage,
    session: AsyncSession = Depends(db_session),
):
    print("Got revocation for: ", body.object_id)
    if body.aspect_type != "delete":
        print("Unknown aspect type for revocation")
        await nats_msg.ack()
        return
    # Will delete user
    nats_conn = broker._connection
    assert nats_conn is not None
    js = nats_conn.jetstream()
    activity_stream_name = ty.cast(str, STREAM_ACTIVITY_CMD.name)
    await js.purge_stream(activity_stream_name, subject=f"rg.internal.cmd.activity.*.{body.object_id}.>")
    user = await session.get(User, body.object_id)
    if user:
        await session.delete(user)
    await session.commit()
    await nats_msg.ack()
    print(f"User {body.object_id} deleted")
