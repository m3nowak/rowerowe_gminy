import typing as ty
from logging import Logger

from faststream import Depends
from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage
from httpx import AsyncClient
from opentelemetry import trace

from rg_app.common.faststream.otel import otel_logger, tracer_fn
from rg_app.common.msg.cmd import StdActivityCmd
from rg_app.common.strava.activities import get_activity
from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.nats_defs.local import CONSUMER_ACTIVITY_CMD_STD, STREAM_ACTIVITY_CMD
from rg_app.worker.deps import http_client, rate_limit_mgr, token_mgr

router = NatsRouter()

stream = JStream(name=ty.cast(str, STREAM_ACTIVITY_CMD.name), declare=False)


@router.subscriber(
    config=CONSUMER_ACTIVITY_CMD_STD,
    stream=stream,
    durable=CONSUMER_ACTIVITY_CMD_STD.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
)
async def std_handle(
    body: StdActivityCmd,  # CreateActivityCmd | UpdateActivityCmd | DeleteActivityCmd,
    broker: NatsBroker,
    nats_msg: NatsMessage,
    http_client: AsyncClient = Depends(http_client),
    rlm: RateLimitManager = Depends(rate_limit_mgr),
    stm: StravaTokenManager = Depends(token_mgr),
    tracer: trace.Tracer = Depends(tracer_fn),
    otel_logger: Logger = Depends(otel_logger),
):
    if body.type in ["create", "update"]:
        with tracer.start_as_current_span("get_auth") as auth_span:
            auth = await stm.get_httpx_auth(body.owner_id)
            auth_span.add_event("auth", {"owner_id": body.owner_id})
        with tracer.start_as_current_span("get_activity") as act_span:
            activity_expanded = await get_activity(http_client, body.activity_id, auth, rlm)
            act_span.add_event("activity_expanded", {"name": activity_expanded.name})
        otel_logger.info(activity_expanded.model_dump_json())
        print("Activity expanded: ", activity_expanded)
        # TODO: Save activity to DB
    elif body.type == "delete":
        pass  # TODO
    await nats_msg.ack()
