from faststream import Context
from faststream.nats import AckPolicy, ConsumerConfig, JStream, NatsBroker, NatsRouter

stream_router = NatsRouter()


stream = JStream(name="test", declare=False)

# Subscribe to a push consumer, with consumer creation
deliver_subject = "stream-test.consume3"
cc = ConsumerConfig(
    durable_name="consumer3",
    deliver_subject=deliver_subject,
    ack_policy=AckPolicy.ALL,
)


@stream_router.subscriber(stream=stream, durable="consumer3")
async def consume(body: str):
    print("message Got: ", body)


# Subscribe to a pull consumer, with consumer creation, and "manual ack", "stream-test.consume4" is the deliver_subject
@stream_router.subscriber("stream-test.consume4", no_reply=True)
async def consume4(body: str, broker: NatsBroker = Context(), reply_to: str = Context("message.reply_to")):
    print(f"message Got in consume4 with reply {reply_to}: {body}")
    await broker.publish(reply_to, "")
