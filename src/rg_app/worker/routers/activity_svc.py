from typing import Literal

import polyline
from faststream.nats import NatsRouter
from faststream.nats.annotations import NatsBroker
from sqlalchemy.exc import NoResultFound

from rg_app.common.internal.activity_svc import DeleteModel, UpsertModel, UpsertModelIneligible
from rg_app.common.internal.geo_svc import GeoSvcCheckRequest, GeoSvcCheckResponse
from rg_app.db.models import Activity, IneligibleActivity
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.dependencies.db import AsyncSessionDI

activity_svc_router = NatsRouter("rg.svc.activity.")

req_check = activity_svc_router.publisher("rg.svc.geo.check", schema=GeoSvcCheckRequest)


@activity_svc_router.subscriber("upsert-ineligible", DEFAULT_QUEUE)
async def upsert_ineligible(
    body: UpsertModelIneligible,
    session: AsyncSessionDI,
) -> Literal["OK"]:
    try:
        activity = await session.get_one(IneligibleActivity, body.id)
        for k, v in body.model_dump(by_alias=False).items():
            if k != "id":
                setattr(activity, k, v)
    except NoResultFound:
        activity = IneligibleActivity(**body.model_dump(by_alias=False))
    session.add(activity)

    activity_old = await session.get(Activity, body.id)
    if activity_old is not None:
        await session.delete(activity_old)

    await session.commit()
    return "OK"


@activity_svc_router.subscriber("upsert", DEFAULT_QUEUE)
async def upsert(
    body: UpsertModel,
    broker: NatsBroker,
    session: AsyncSessionDI,
) -> Literal["OK"]:
    try:
        activity = await session.get_one(Activity, body.id)
    except NoResultFound:
        activity = None

    polyline_str = body.polyline

    geojson_list = polyline.decode(polyline_str, precision=5, geojson=True)

    resp = await broker.request(GeoSvcCheckRequest(coordinates=geojson_list), "rg.svc.geo.check", timeout=30)

    resp_parsed = GeoSvcCheckResponse.model_validate_json(resp.body)
    main_regions = [x.id for x in resp_parsed.items if x.type == "GMI"]
    additional_regions = [x.id for x in resp_parsed.items if x.type != "GMI"]
    dct = body.model_dump(by_alias=False)
    dct.pop("polyline")

    dct["track"] = geojson_list
    dct["visited_regions"] = main_regions
    dct["visited_regions_additional"] = additional_regions

    if activity is None:
        activity = Activity(**dct)
    else:
        for k, v in dct.items():
            if k != "id":
                setattr(activity, k, v)
    session.add(activity)

    activity_ineligible = await session.get(IneligibleActivity, body.id)
    if activity_ineligible is not None:
        await session.delete(activity_ineligible)

    await session.commit()
    return "OK"


@activity_svc_router.subscriber("delete", DEFAULT_QUEUE)
async def delete(
    body: DeleteModel,
    session: AsyncSessionDI,
) -> Literal["OK"]:
    activity = await session.get(Activity, body.id)
    if not activity:
        return "OK"
    assert activity.user_id == body.user_id
    await session.delete(activity)
    await session.commit()
    return "OK"
