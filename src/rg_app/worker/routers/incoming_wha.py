import typing as ty

from faststream import Context, Depends
from faststream.nats import JStream, NatsBroker, NatsMessage, NatsRouter
from faststream.opentelemetry import CurrentSpan
from httpx import AsyncClient
from opentelemetry import trace

from rg_app.common.strava.activities import get_activity
from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.models.webhook import WebhookActivity
from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.nats_defs.local import CONSUMER_ACTIVITIES, NAME_INCOMING_WHA_MIRROR
from rg_app.worker.deps import http_client, rate_limit_mgr, token_mgr
from rg_app.worker.otel import otel_logger, tracer_fn

incoming_wha_router = NatsRouter()

stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)


@incoming_wha_router.subscriber(ty.cast(str, CONSUMER_ACTIVITIES.deliver_subject), no_reply=True)
async def activities(
    body: WebhookActivity,
    msg: NatsMessage,
    span: CurrentSpan,
    broker: NatsBroker = Context(),
    reply_to: str = Context("message.reply_to"),
    http_client: AsyncClient = Depends(http_client),
    rlm: RateLimitManager = Depends(rate_limit_mgr),
    stm: StravaTokenManager = Depends(token_mgr),
    tracer: trace.Tracer = Depends(tracer_fn),
    otel_logger=Depends(otel_logger),
):
    # print(f"message Got in activities with reply {reply_to}: {body}")
    with tracer.start_as_current_span("get_auth") as auth_span:
        auth = await stm.get_httpx_auth(body.owner_id)
        auth_span.add_event("auth", {"owner_id": body.owner_id})
    with tracer.start_as_current_span("get_activity") as act_span:
        activity_expanded = await get_activity(http_client, body.object_id, auth, rlm)
        act_span.add_event("activity_expanded", {"name": activity_expanded.name})
    otel_logger.info(activity_expanded.model_dump_json())
    await broker.publish("+ACK", reply_to)


# # This does not work, delivery subject is replaced
# @webhook_router.subscriber(stream=stream, config=CONSUMER_ACTIVITIES)
# async def consume(body: str):
#     print("message Got: ", body)
