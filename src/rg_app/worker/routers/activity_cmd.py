import typing as ty
from decimal import Decimal
from logging import Logger

import polyline
from faststream import Depends
from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage
from httpx import AsyncClient
from opentelemetry import trace

from rg_app.common.faststream.otel import otel_logger, tracer_fn
from rg_app.common.internal import activity_filter
from rg_app.common.internal.activity_svc import DeleteModel, UpsertModel
from rg_app.common.internal.geo_svc import GeoSvcCheckRequest, GeoSvcCheckResponse
from rg_app.common.msg.cmd import BacklogActivityCmd, StdActivityCmd
from rg_app.common.strava.activities import get_activity
from rg_app.common.strava.auth import StravaTokenManager
from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.nats_defs.local import CONSUMER_ACTIVITY_CMD_BACKLOG, CONSUMER_ACTIVITY_CMD_STD, STREAM_ACTIVITY_CMD
from rg_app.worker.deps import http_client, rate_limit_mgr, token_mgr

router = NatsRouter()

stream = JStream(name=ty.cast(str, STREAM_ACTIVITY_CMD.name), declare=False)

req_upsert = router.publisher("rg.svc.activity.upsert", schema=UpsertModel)
req_delete = router.publisher("rg.svc.activity.delete", schema=DeleteModel)
req_check = router.publisher("rg.svc.geo.check", schema=GeoSvcCheckRequest)


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
):
    raise NotImplementedError("Backlog processing is not implemented yet")


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
    span = trace.get_current_span()
    if body.type in ["create", "update"]:
        with tracer.start_as_current_span("get_auth") as auth_span:
            auth = await stm.get_httpx_auth(body.owner_id)
            auth_span.add_event("auth", {"owner_id": body.owner_id})
        with tracer.start_as_current_span("get_activity") as act_span:
            activity_expanded = await get_activity(http_client, body.activity_id, auth, rlm)
            act_span.add_event("activity_expanded", {"name": activity_expanded.name})
        otel_logger.info(activity_expanded.model_dump_json())
        is_ok, reason = activity_filter(activity_expanded)
        if not is_ok:
            reason = reason or "Unknown"
            span.add_event("activity_filter_failed", {"reason": reason})
            print(f"Activity {body.activity_id} filtered out: {reason}")
            await nats_msg.ack()
            return

        assert activity_expanded.map is not None
        polyline_str = (
            activity_expanded.map.summary_polyline if body.type == "create" else activity_expanded.map.polyline
        )
        assert polyline_str is not None

        geojson_list = polyline.decode(polyline_str, precision=5, geojson=True)

        resp = await req_check.request(GeoSvcCheckRequest(coordinates=geojson_list), timeout=30)
        resp_parsed = GeoSvcCheckResponse.model_validate_json(resp.body)
        main_regions = [x.id for x in resp_parsed.items if x.type == "GMI"]
        additional_regions = [x.id for x in resp_parsed.items if x.type != "GMI"]
        span.set_attribute("main_regions", len(main_regions))
        span.set_attribute("additional_regions", len(additional_regions))

        activity_model = UpsertModel(
            id=activity_expanded.id,
            user_id=activity_expanded.athlete.id,
            name=activity_expanded.name,
            manual=activity_expanded.manual,
            start=activity_expanded.start_date,
            moving_time=activity_expanded.moving_time,
            elapsed_time=activity_expanded.elapsed_time,
            distance=ty.cast(Decimal, activity_expanded.distance),
            track=geojson_list,
            track_is_detailed=body.type == "update",
            elevation_gain=activity_expanded.total_elevation_gain,
            elevation_high=activity_expanded.elev_high,
            elevation_low=activity_expanded.elev_low,
            type=activity_expanded.type,
            sport_type=activity_expanded.sport_type,
            gear_id=activity_expanded.gear_id,
            visited_regions=main_regions,
            visited_regions_additional=additional_regions,
        )

        resp = await req_upsert.request(activity_model, timeout=30)
        resp_parsed = resp.body.decode()
        assert resp_parsed == "OK"
        span.set_attribute("activity_id", activity_model.id)
        print(f"Activity {body.activity_id} processed!")
    elif body.type == "delete":
        resp = await req_delete.request(DeleteModel(id=body.activity_id, user_id=body.owner_id), timeout=30)
        resp_parsed = resp.body.decode()
        assert resp_parsed == "OK"
        print(f"Activity {body.activity_id} deleted!")
    await nats_msg.ack()
