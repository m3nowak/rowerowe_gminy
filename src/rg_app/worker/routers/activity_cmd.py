import typing as ty
from decimal import Decimal
from logging import Logger

from faststream import Depends
from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsBroker, NatsMessage
from httpx import AsyncClient, HTTPStatusError
from opentelemetry import trace
from sqlalchemy import and_, func, not_, select

from rg_app.api.dependencies.db import AsyncSession
from rg_app.common.enums import DescUpdateOptions
from rg_app.common.faststream.otel import otel_logger, tracer_fn
from rg_app.common.internal import activity_filter
from rg_app.common.internal.activity_svc import DeleteModel, UpsertModel, UpsertModelIneligible
from rg_app.common.msg.cmd import BacklogActivityCmd, StdActivityCmd
from rg_app.common.strava.activities import get_activity, get_activity_range, update_activity
from rg_app.common.strava.auth import StravaAuth, StravaTokenManager
from rg_app.common.strava.models.activity import ActivityPartial, ActivityPatch
from rg_app.common.strava.rate_limits import RateLimitManager
from rg_app.db.models import User
from rg_app.db.models.models import Activity, Region
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
    auth = await stm.get_httpx_auth(body.owner_id)

    user = await session.get(User, body.owner_id)
    if user is None:
        otel_logger.error(f"User {body.owner_id} not found")
        await nats_msg.ack()
        return
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
            # republish activity, for std handle
            activity_cmd = StdActivityCmd(
                owner_id=activity.athlete.id,
                activity_id=activity.id,
                type="create",
                activity=activity,
                is_from_backlog=True,
            )
            subject = f"rg.internal.cmd.activity.create.{activity.athlete.id}.{activity.id}"

            await pub_activity_std.publish(activity_cmd, subject)
    await nats_msg.ack()


DESC_SECTION_START = "RoweroweGminy.pl 🏘️🚴🇵🇱"
DESC_SECTION_END = "---"
DESC_TOWN_HEADER = "🏙️ Zdobyte Miasta :"
DESC_COMMUNE_HEADER = "🏡 Zdobyte Gminy :"


def _declinate_commune(count: int) -> str:
    if count == 1:
        return "gmina"
    elif count == 2 or count == 3 or count == 4:
        return "gminy"
    else:
        return "gmin"


def _declinate_new(count: int) -> str:
    if count == 1:
        return "nową"
    elif count == 2 or count == 3 or count == 4:
        return "nowe"
    else:
        return "nowych"


async def _get_activity_description_content(session: AsyncSession, db_activity: Activity) -> list[str]:
    """
    Generate activity description content with commune and town information.
    Returns a list of lines to be inserted in the activity description.
    """
    # Target record CTE
    target_record_cte = (
        select(Activity.id, Activity.user_id, Activity.visited_regions, Activity.start)
        .where(Activity.id == db_activity.id)
        .cte("target_record")
    )

    # Earlier regions CTE
    earlier_regions_cte = (
        select(func.jsonb_array_elements_text(Activity.visited_regions).label("region"))
        .select_from(Activity)
        .join(
            target_record_cte,
            and_(
                Activity.user_id == target_record_cte.c.user_id,
                Activity.start < target_record_cte.c.start,
                Activity.id != target_record_cte.c.id,
            ),
        )
        .distinct()
        .cte("earlier_regions")
    )

    # Target record array elements CTE
    target_regions_cte = select(
        func.jsonb_array_elements_text(target_record_cte.c.visited_regions).label("region")
    ).cte("target_record_ael")

    # Final query - find regions in target activity that aren't in earlier activities
    new_regions_query = (
        select(target_regions_cte.c.region, Region.name)
        .select_from(target_regions_cte.join(Region, target_regions_cte.c.region == Region.id))
        .where(not_(target_regions_cte.c.region.in_(select(earlier_regions_cte.c.region))))
    )

    # Execute the query to get the new regions
    result = await session.execute(new_regions_query)
    new_communes = []
    new_towns = []
    for row in result:
        region_id: str = row[0]
        region_name = row[1]
        if not region_name:
            # Region not found in DB or is nameless, skip it
            continue
        if region_id.endswith("1"):
            new_towns.append((region_id, region_name))
        else:
            new_communes.append((region_id, region_name))
    activity_new_count = len(new_communes) + len(new_towns)
    activity_total_count = len(db_activity.visited_regions)

    so_far_regions_cte = (
        select(target_regions_cte.c.region).union(select(earlier_regions_cte.c.region)).cte("total_regions")
    )
    so_far_regions_unique_cte = select(so_far_regions_cte.c.region).distinct().cte("total_regions_unique")
    so_far_regions_unique_count_result = await session.execute(
        select(func.count(so_far_regions_unique_cte.c.region).label("count"))
    )
    so_far_regions_unique_count = so_far_regions_unique_count_result.scalar_one_or_none() or 0

    total_achievable_count = await session.execute(
        select(func.count(Region.id).label("count")).where(
            Region.type == "GMI",
        )
    )
    total_achievable_count = total_achievable_count.scalar_one_or_none() or 0

    desc_lines = []
    desc_lines.append(DESC_SECTION_START)
    fline = f"Odwiedzono {activity_total_count} {_declinate_commune(activity_total_count)}"
    if activity_new_count:
        fline += f", w tym {activity_new_count} {_declinate_new(activity_new_count)}!"
    else:
        fline += "."
    desc_lines.append(fline)
    if new_towns:
        desc_lines.append(DESC_TOWN_HEADER)
        for _, name in new_towns:
            desc_lines.append(f"- {name}")
    if new_communes:
        desc_lines.append(DESC_COMMUNE_HEADER)
        for _, name in new_communes:
            desc_lines.append(f"- gmina {name}")
    achieved_percent = "{:.3f}%".format(100 * so_far_regions_unique_count / total_achievable_count)
    desc_lines.append(
        f"Przejechano do tej pory {so_far_regions_unique_count} {_declinate_commune(so_far_regions_unique_count)} z {total_achievable_count}! ({achieved_percent})"
    )
    desc_lines.append(DESC_SECTION_END)
    return desc_lines


async def _update_activity_desc(
    session: AsyncSession,
    http_client: AsyncClient,
    activity: ActivityPartial,
    auth: StravaAuth,
    rlm: RateLimitManager,
) -> None:
    """
    Update activity description in strava.
    Has to be called after activity is created in DB.
    """
    db_activity = await session.get_one(Activity, activity.id)
    if not db_activity.visited_regions:
        # No regions visited, no need to update desc
        return

    desc_content = await _get_activity_description_content(session, db_activity)

    activity_desc_lines = (activity.description or "").splitlines()
    start_idx = -1
    end_idx = -1
    try:
        start_idx = activity_desc_lines.index(DESC_SECTION_START)
        end_idx = activity_desc_lines[start_idx:].index(DESC_SECTION_END) + start_idx
    except ValueError:
        # No existing section, need to add it at the end
        pass

    if start_idx == -1 and end_idx == -1:
        activity_desc_lines.extend(desc_content)

    elif start_idx != -1 and end_idx != -1:
        # update section
        activity_desc_lines = activity_desc_lines[:start_idx] + desc_content + activity_desc_lines[end_idx + 1 :]
    else:
        # malformed section, skip
        return

    # Update activity description
    await update_activity(
        http_client,
        activity.id,
        auth,
        rlm,
        ActivityPatch(
            description="\n".join(activity_desc_lines),
        ),
    )


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
    session: AsyncSession = Depends(db_session),
):
    span = trace.get_current_span()
    if body.type in ["create", "update"]:
        user_id = body.owner_id
        user = await session.get(User, user_id)
        if user is None:
            otel_logger.error(
                f"User {user_id} not found, skipping activity {body.activity_id}",
                extra={"user_id": user_id, "activity_id": body.activity_id},
            )
            await nats_msg.ack()
            return
        auth = None
        if body.activity is None:
            auth = await stm.get_httpx_auth(body.owner_id)
            with tracer.start_as_current_span("get_activity") as act_span:
                activity_expanded = await get_activity(http_client, body.activity_id, auth, rlm)
                if activity_expanded:
                    act_span.add_event(
                        "activity_expanded", {"name": activity_expanded.name, "id": body.activity_id, "user": user_id}
                    )
                else:
                    act_span.add_event("activity_missing", {"id": body.activity_id, "user": user_id})
                    print(f"Activity {body.activity_id} not found, skipping!")
                    await nats_msg.ack()
                    return
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

            # Acitivity desc update
            update_desc = DescUpdateOptions(user.update_strava_desc)
            if update_desc != DescUpdateOptions.NONE and not body.is_from_backlog:
                if auth is None:
                    auth = await stm.get_httpx_auth(body.owner_id)
                try:
                    await _update_activity_desc(session, http_client, activity_expanded, auth, rlm)
                except HTTPStatusError as e:
                    if e.response.status_code == 401:
                        # User not authorized to update activity
                        print(f"User {user_id} not authorized to update activity {body.activity_id}")
                        otel_logger.error(
                            f"User {user_id} not authorized to update activity {body.activity_id}",
                            extra={"user_id": user_id, "activity_id": body.activity_id},
                        )
                    else:
                        span.record_exception(e)
                        otel_logger.error(
                            f"Failed to update activity {body.activity_id} description: {e}",
                            extra={"user_id": user_id, "activity_id": body.activity_id},
                        )
                        await nats_msg.nack()
                        return
                print(f"Activity {body.activity_id} description updated!")

            print(f"Activity {body.activity_id} processed!")
    elif body.type == "delete":
        resp = await req_delete.request(DeleteModel(id=body.activity_id, user_id=body.owner_id), timeout=30)
        resp_parsed = resp.body.decode()
        assert resp_parsed == "OK"
        print(f"Activity {body.activity_id} deleted!")
    await nats_msg.ack()
