from typing import cast

import fastapi
from nats.js.api import ConsumerConfig, DeliverPolicy

from rg_app.api.common import user_check_last_trigger
from rg_app.api.dependencies.auth import UserInfoRequired
from rg_app.api.dependencies.broker import NatsClient
from rg_app.api.dependencies.db import AsyncSession
from rg_app.api.models.athletes import AthleteDetail
from rg_app.db.models import User
from rg_app.nats_defs.local import CONSUMER_ACTIVITY_CMD_STD, STREAM_ACTIVITY_CMD

router = fastapi.APIRouter(tags=["athletes"], prefix="/athletes")


@router.get("/me")
async def get_logged_in_user(
    user_info: UserInfoRequired,
    session: AsyncSession,
    nats_client: NatsClient,
) -> AthleteDetail:
    user_id = user_info.user_id
    user = await session.get(User, user_id)
    assert user is not None

    js = nats_client.jetstream()
    stream_name = cast(str, STREAM_ACTIVITY_CMD.name)
    consumer_name_og = cast(str, CONSUMER_ACTIVITY_CMD_STD.name)
    # rg.internal.cmd.activity.{type}.{athlete_id}.{activity_id?}
    consumer_og = await js.consumer_info(stream_name, consumer_name_og)
    consumer = await js.add_consumer(
        stream=stream_name,
        config=ConsumerConfig(
            filter_subjects=[
                f"rg.internal.cmd.activity.*.{user_id}.*",
                f"rg.internal.cmd.activity.*.{user_id}",
            ],
            opt_start_seq=consumer_og.ack_floor.stream_seq + 1 if consumer_og.ack_floor else None,
            deliver_policy=DeliverPolicy.BY_START_SEQUENCE,
        ),
    )
    unprocessed_activities = consumer.num_pending or 0
    await js.delete_consumer(stream_name, consumer.name)

    return AthleteDetail(
        id=user_id,
        created_at=user.strava_account_created_at,
        last_backlog_sync=user.last_backlog_sync,
        backlog_sync_eligible=user_check_last_trigger(user),
        strava_account_created_at=user.strava_account_created_at,
        unprocessed_activities=unprocessed_activities,
    )
