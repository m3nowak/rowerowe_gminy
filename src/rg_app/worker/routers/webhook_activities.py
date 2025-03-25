import typing as ty

from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage

from rg_app.common.msg.cmd import StdActivityCmd
from rg_app.common.strava.models.webhook import WebhookActivity
from rg_app.nats_defs.local import (
    CONSUMER_ACTIVITIES,
    NAME_INCOMING_WHA_MIRROR,
    STREAM_ACTIVITY_CMD,
)
from rg_app.nats_defs.subjects import internal_cmd_activity_subject

router = NatsRouter()

wha_stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)
activity_cmd_stream = JStream(name=ty.cast(str, STREAM_ACTIVITY_CMD.name), declare=False)

publisher = router.publisher("rg.internal.cmd.activity.*.*.*", stream=activity_cmd_stream.name, schema=StdActivityCmd)


@router.subscriber(
    subject="an1",
    config=CONSUMER_ACTIVITIES,
    stream=wha_stream,
    durable=CONSUMER_ACTIVITIES.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
    title=f"{wha_stream.name}/{CONSUMER_ACTIVITIES.durable_name}",
)
async def activities_handle(
    body: WebhookActivity,
    broker: NatsBroker,
    nats_msg: NatsMessage,
):
    print("Got activity: ", body.object_id)
    if body.aspect_type in ["create", "update", "delete"]:
        msg = StdActivityCmd(owner_id=body.owner_id, activity_id=body.object_id, type=body.aspect_type)
    else:
        raise ValueError("Unknown aspect type")
    subject = internal_cmd_activity_subject(msg.type, msg.owner_id, msg.activity_id)
    await publisher.publish(msg, subject)
    await nats_msg.ack()


# @router.subscriber(
#     config=CONSUMER_REVOCATIONS,
#     stream=wha_stream,
#     durable=CONSUMER_REVOCATIONS.durable_name,
#     pull_sub=PullSub(batch_size=1),
#     no_ack=True,
#     # title=f"{wha_stream.name}/{CONSUMER_REVOCATIONS.durable_name}",
# )
# async def revocations_handle(
#     body: WebhookAthlete,
#     # broker: NatsBroker,
#     # nats_msg: NatsMessage,
#     # session: AsyncSession = Depends(db_session),
# ):
#     print("Got revocation for: ", body.object_id)
#     if body.aspect_type != "delete":
#         print("Unknown aspect type for revocation")
#         # await nats_msg.ack()
#         return
#     # Will delete user
#     # nats_conn = broker._connection
#     # assert nats_conn is not None
#     # js = nats_conn.jetstream()
#     # activity_stream_name = ty.cast(str, STREAM_ACTIVITY_CMD.name)
#     # await js.purge_stream(activity_stream_name, subject=f"rg.internal.cmd.activity.*.{body.object_id}.>")
#     # user = await session.get(User, body.object_id)
#     # if user:
#     #     await session.delete(user)
#     # await session.commit()
#     # await nats_msg.ack()
#     print(f"User {body.object_id} deleted")
