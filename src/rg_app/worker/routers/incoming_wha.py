import asyncio
import typing as ty

from faststream import Context, Depends
from faststream.nats import JStream, NatsBroker, NatsMessage, NatsRouter
from httpx import AsyncClient

from rg_app.common.strava.models.webhook import WebhookActivity
from rg_app.nats_defs.local import CONSUMER_ACTIVITIES, NAME_INCOMING_WHA_MIRROR
from rg_app.worker.deps import http_client

incoming_wha_router = NatsRouter()


stream = JStream(name=ty.cast(str, NAME_INCOMING_WHA_MIRROR), declare=False)


@incoming_wha_router.subscriber(ty.cast(str, CONSUMER_ACTIVITIES.deliver_subject), no_reply=True)
async def activities(
    body: WebhookActivity,
    msg: NatsMessage,
    broker: NatsBroker = Context(),
    reply_to: str = Context("message.reply_to"),
    http_client: AsyncClient = Depends(http_client),
):
    print(f"message Got in consume4 with reply {reply_to}: {body}")
    await asyncio.sleep(3)
    await msg.nack(10)


# # This does not work, delivery subject is replaced
# @webhook_router.subscriber(stream=stream, config=CONSUMER_ACTIVITIES)
# async def consume(body: str):
#     print("message Got: ", body)
