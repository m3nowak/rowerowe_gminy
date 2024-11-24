from typing import Literal

from faststream import Depends
from faststream.nats import NatsRouter
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from rg_app.common.internal.activity_svc import UpsertModel
from rg_app.db.models import Activity
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.deps import db_session

activity_svc_router = NatsRouter("rg.svc.activity.")


@activity_svc_router.subscriber("upsert", DEFAULT_QUEUE)
async def upsert(
    body: UpsertModel,
    session: AsyncSession = Depends(db_session),
) -> Literal["OK"]:
    try:
        activity = await session.get_one(Activity, body.id)
    except NoResultFound:
        activity = None
    dct = body.model_dump(by_alias=False)
    if activity is None:
        activity = Activity(**dct)
    else:
        for k, v in dct.items():
            setattr(activity, k, v)
    session.add(activity)
    await session.commit()
    return "OK"
