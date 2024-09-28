from faststream.nats import AckPolicy, ConsumerConfig, JStream, NatsRouter

stream_router = NatsRouter()


stream = JStream(name="test", declare=False)

cc = ConsumerConfig(durable_name="consumer1", deliver_subject="stream-test.consume", ack_policy=AckPolicy.ALL)


@stream_router.subscriber(stream=stream, config=cc)
async def consume(body: str):
    print("message Got: ", body)
