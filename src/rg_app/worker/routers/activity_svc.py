from typing import Literal

import polyline
from faststream import Depends
from faststream.nats import NatsRouter
from faststream.nats.annotations import NatsBroker
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.internal.activity_svc import DeleteModel, UpsertModel
from rg_app.common.internal.geo_svc import GeoSvcCheckRequest, GeoSvcCheckResponse
from rg_app.db.models import Activity
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.deps import db_session

activity_svc_router = NatsRouter("rg.svc.activity.")

req_check = activity_svc_router.publisher("rg.svc.geo.check", schema=GeoSvcCheckRequest)


@activity_svc_router.subscriber("upsert", DEFAULT_QUEUE)
async def upsert(
    body: UpsertModel,
    broker: NatsBroker,
    session: AsyncSession = Depends(db_session),
) -> Literal["OK"]:
    try:
        activity = await session.get_one(Activity, body.id)
    except NoResultFound:
        activity = None

    polyline_str = body.polyline

    geojson_list = polyline.decode(polyline_str, precision=5, geojson=True)

    resp = await broker.request(GeoSvcCheckRequest(coordinates=geojson_list), "rg.svc.geo.check", timeout=30)

    # resp = await req_check.request(GeoSvcCheckRequest(coordinates=geojson_list), timeout=30)
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
    await session.commit()
    return "OK"


@activity_svc_router.subscriber("delete", DEFAULT_QUEUE)
async def delete(
    body: DeleteModel,
    session: AsyncSession = Depends(db_session),
) -> Literal["OK"]:
    activity = await session.get_one(Activity, body.id)
    assert activity.user_id == body.user_id
    await session.delete(activity)
    await session.commit()
    return "OK"
