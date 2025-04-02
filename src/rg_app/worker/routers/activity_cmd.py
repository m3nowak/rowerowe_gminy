import typing as ty
from decimal import Decimal
from logging import Logger

from faststream import Depends
from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage
from httpx import AsyncClient
from opentelemetry import trace

from rg_app.api.dependencies.db import AsyncSession
from rg_app.common.faststream.otel import otel_logger, tracer_fn
from rg_app.common.internal import activity_filter
from rg_app.common.internal.activity_svc import DeleteModel, UpsertModel, UpsertModelIneligible
from rg_app.common.msg.cmd import BacklogActivityCmd, StdActivityCmd
from rg_app.common.strava.activities import get_activity, get_activity_range
from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.models.activity import ActivityPartial
from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.db.models import User
from rg_app.nats_defs.local import CONSUMER_ACTIVITY_CMD_BACKLOG, CONSUMER_ACTIVITY_CMD_STD, STREAM_ACTIVITY_CMD
from rg_app.worker.deps import db_session, http_client, rate_limit_mgr, token_mgr

router = NatsRouter()

stream = JStream(name=ty.cast(str, STREAM_ACTIVITY_CMD.name), declare=False)

pub_activity_std = router.publisher("rg.internal.cmd.activity.create.{athlete_id}.{activity_id}", stream=stream)

req_upsert = router.publisher("rg.svc.activity.upsert", schema=UpsertModel)
req_upsert_ineligible = router.publisher("rg.svc.activity.upsert-ineligible", schema=UpsertModel)
req_delete = router.publisher("rg.svc.activity.delete", schema=DeleteModel)


def _mk_ineligible_activity(activity: ActivityPartial, reason: str) -> UpsertModelIneligible:
    return UpsertModelIneligible(
        id=activity.id,
        user_id=activity.athlete.id,
        name=activity.name,
        reject_reason=reason,
        start=activity.start_date,
    )


def _mk_upsert_model(activity: ActivityPartial, polyline_str: str, is_detailed: bool) -> UpsertModel:
    activity_model = UpsertModel(
        id=activity.id,
        user_id=activity.athlete.id,
        name=activity.name,
        manual=activity.manual,
        start=activity.start_date,
        moving_time=activity.moving_time,
        elapsed_time=activity.elapsed_time,
        distance=ty.cast(Decimal, activity.distance),
        track_is_detailed=is_detailed,
        elevation_gain=activity.total_elevation_gain,
        elevation_high=activity.elev_high,
        elevation_low=activity.elev_low,
        sport_type=activity.sport_type,
        gear_id=activity.gear_id,
        polyline=polyline_str,
        full_data=activity.original_data,
    )

    return activity_model


@router.subscriber(
    config=CONSUMER_ACTIVITY_CMD_BACKLOG,
    stream=stream,
    durable=CONSUMER_ACTIVITY_CMD_BACKLOG.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
)
async def backlog_handle(
    body: BacklogActivityCmd,
    broker: NatsBroker,
    nats_msg: NatsMessage,
    http_client: AsyncClient = Depends(http_client),
    rlm: RateLimitManager = Depends(rate_limit_mgr),
    stm: StravaTokenManager = Depends(token_mgr),
    tracer: trace.Tracer = Depends(tracer_fn),
    otel_logger: Logger = Depends(otel_logger),
    session: AsyncSession = Depends(db_session),
):
    span = trace.get_current_span()
    with tracer.start_as_current_span("get_auth") as auth_span:
        auth = await stm.get_httpx_auth(body.owner_id)
        auth_span.add_event("auth", {"owner_id": body.owner_id})

    user = await session.get(User, body.owner_id)
    if user is None:
        otel_logger.error(f"User {body.owner_id} not found")
        await nats_msg.ack()
    has_more = True
    page = 0
    while has_more:
        activity_range = await get_activity_range(http_client, body.period_from, body.period_to, page, auth, rlm)
        has_more = activity_range.has_more
        page += 1
        if page >= 50:
            print("Too many pages!")
            break
        for activity in activity_range.items:
            # republish actvity, for std handle

            activity_cmd = StdActivityCmd(
                owner_id=activity.athlete.id, activity_id=activity.id, type="create", activity=activity
            )
            subject = f"rg.internal.cmd.activity.create.{activity.athlete.id}.{activity.id}"

            await pub_activity_std.publish(activity_cmd, subject)
    await nats_msg.ack()


@router.subscriber(
    config=CONSUMER_ACTIVITY_CMD_STD,
    stream=stream,
    durable=CONSUMER_ACTIVITY_CMD_STD.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
)
async def std_handle(
    body: StdActivityCmd,
    broker: NatsBroker,
    nats_msg: NatsMessage,
    http_client: AsyncClient = Depends(http_client),
    rlm: RateLimitManager = Depends(rate_limit_mgr),
    stm: StravaTokenManager = Depends(token_mgr),
    tracer: trace.Tracer = Depends(tracer_fn),
    otel_logger: Logger = Depends(otel_logger),
):
    span = trace.get_current_span()
    if body.type in ["create", "update"]:
        with tracer.start_as_current_span("get_auth") as auth_span:
            auth = await stm.get_httpx_auth(body.owner_id)
            auth_span.add_event("auth", {"owner_id": body.owner_id})
        if body.activity is None:
            with tracer.start_as_current_span("get_activity") as act_span:
                activity_expanded = await get_activity(http_client, body.activity_id, auth, rlm)
                act_span.add_event("activity_expanded", {"name": activity_expanded.name})
        else:
            activity_expanded = body.activity
        otel_logger.info(activity_expanded.model_dump_json())
        span.set_attribute("activity_id", activity_expanded.id)
        is_eligible, reason = activity_filter(activity_expanded)
        if not is_eligible:
            reason = reason or "Unknown"
            span.add_event("activity_filter_failed", {"reason": reason, "activity_id": body.activity_id})
            print(f"Activity {body.activity_id} filtered out: {reason}")
            umi = _mk_ineligible_activity(activity_expanded, reason)
            resp = await req_upsert_ineligible.request(umi, timeout=30)
            resp_parsed = resp.body.decode()
            assert resp_parsed == "OK"
            print(f"Activity {body.activity_id} processed as ineligible ({reason})!")
        else:
            assert activity_expanded.map is not None
            polyline_str = (
                activity_expanded.map.summary_polyline if body.type == "create" else activity_expanded.map.polyline
            )
            assert polyline_str is not None

            activity_model = _mk_upsert_model(activity_expanded, polyline_str, body.type == "update")

            resp = await req_upsert.request(activity_model, timeout=30)
            resp_parsed = resp.body.decode()
            assert resp_parsed == "OK"
            print(f"Activity {body.activity_id} processed!")
    elif body.type == "delete":
        resp = await req_delete.request(DeleteModel(id=body.activity_id, user_id=body.owner_id), timeout=30)
        resp_parsed = resp.body.decode()
        assert resp_parsed == "OK"
        print(f"Activity {body.activity_id} deleted!")
    await nats_msg.ack()
