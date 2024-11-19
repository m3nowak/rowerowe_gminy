import typing as ty

from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage

from rg_app.common.msg.cmd import StdActivityCmd
from rg_app.common.strava.models.webhook import WebhookActivity
from rg_app.nats_defs.local import CONSUMER_ACTIVITIES, NAME_INCOMING_WHA_MIRROR, STREAM_ACTIVITY_CMD
from rg_app.nats_defs.subjects import internal_cmd_activity_subject

incoming_wha_router = NatsRouter()

wha_stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)
activity_cmd_stream = JStream(name=ty.cast(str, STREAM_ACTIVITY_CMD.name), declare=False)

publisher = incoming_wha_router.publisher("rg.internal.cmd.activity.*.*.*", stream=activity_cmd_stream.name)


@incoming_wha_router.subscriber(
    config=CONSUMER_ACTIVITIES,
    stream=wha_stream,
    durable=CONSUMER_ACTIVITIES.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
)
async def activities_handle(
    body: WebhookActivity,
    broker: NatsBroker,
    nats_msg: NatsMessage,
):
    print("Got activity: ", body)
    if body.aspect_type in ["create", "update", "delete"]:
        msg = StdActivityCmd(owner_id=body.owner_id, activity_id=body.object_id, type=body.aspect_type)
    else:
        raise ValueError("Unknown aspect type")
    # msg_serialized = msg.model_dump_json(by_alias=True)
    subject = internal_cmd_activity_subject(msg.type, msg.owner_id, msg.activity_id)
    await publisher.publish(msg, subject)
    # await broker.publish(msg_serialized, subject, stream=activity_cmd_stream.name)
    await nats_msg.ack()


# @incoming_wha_router.subscriber(ty.cast(str, CONSUMER_ACTIVITIES.deliver_subject), no_reply=True)
# async def activities(
#     body: WebhookActivity,
#     msg: NatsMessage,
#     span: CurrentSpan,
#     broker: NatsBroker = Context(),
#     reply_to: str = Context("message.reply_to"),
#     http_client: AsyncClient = Depends(http_client),
#     rlm: RateLimitManager = Depends(rate_limit_mgr),
#     stm: StravaTokenManager = Depends(token_mgr),
#     tracer: trace.Tracer = Depends(tracer_fn),
#     otel_logger=Depends(otel_logger),
# ):
#     return

#     # Below code is for getting activities from strava, it stays here for now

#     with tracer.start_as_current_span("get_auth") as auth_span:
#         auth = await stm.get_httpx_auth(body.owner_id)
#         auth_span.add_event("auth", {"owner_id": body.owner_id})
#     with tracer.start_as_current_span("get_activity") as act_span:
#         activity_expanded = await get_activity(http_client, body.object_id, auth, rlm)
#         act_span.add_event("activity_expanded", {"name": activity_expanded.name})
#     otel_logger.info(activity_expanded.model_dump_json())
#     await broker.publish("+ACK", reply_to)


# # This does not work, delivery subject is replaced
# @webhook_router.subscriber(stream=stream, config=CONSUMER_ACTIVITIES)
# async def consume(body: str):
#     print("message Got: ", body)
