import typing as ty

from faststream import Context
from faststream.nats import JStream, NatsBroker, NatsRouter

from rg_app.nats_defs.cloud import CONSUMER_ACTIVITIES, STREAM_INCOMING_WHA

webhook_router = NatsRouter()


stream = JStream(name=ty.cast(str, STREAM_INCOMING_WHA.name), declare=False)


@webhook_router.subscriber(ty.cast(str, CONSUMER_ACTIVITIES.deliver_subject), no_reply=True)
async def activities(body: str, broker: NatsBroker = Context(), reply_to: str = Context("message.reply_to")):
    print(f"message Got in consume4 with reply {reply_to}: {body}")
    await broker.publish("", reply_to)


# # This does not work, delivery subject is replaced
# @webhook_router.subscriber(stream=stream, config=CONSUMER_ACTIVITIES)
# async def consume(body: str):
#     print("message Got: ", body)
