import typing as ty

from faststream.nats import JStream, NatsRouter, PullSub
from faststream.nats.annotations import NatsMessage

from rg_app.common.internal.user_svc import AccountDeleteRequest
from rg_app.common.strava.models.webhook import WebhookAthlete
from rg_app.nats_defs.local import (
    CONSUMER_REVOCATIONS,
    NAME_INCOMING_WHA_MIRROR,
)

router = NatsRouter()

wha_stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)
publisher = router.publisher("rg.svc.user.delete-account", schema=AccountDeleteRequest)


@router.subscriber(
    subject="an2",
    config=CONSUMER_REVOCATIONS,
    stream=wha_stream,
    durable=CONSUMER_REVOCATIONS.durable_name,
    pull_sub=PullSub(),
    no_ack=True,
    title=f"{wha_stream.name}/{CONSUMER_REVOCATIONS.durable_name}",
)
async def revocations_handle(
    body: WebhookAthlete,
    nats_msg: NatsMessage,
):
    print("Got revocation for: ", body.object_id)
    if body.aspect_type != "delete":
        print("Unknown aspect type for revocation")
        await nats_msg.ack()
        return
    # Will delete user
    resp = await publisher.request(AccountDeleteRequest(user_id=body.object_id))
    if resp.body.decode() != "OK":
        print(f"Failed to delete user {body.object_id}")
        await nats_msg.nack()
    else:
        await nats_msg.ack()
