from nats.js import JetStreamManager
from nats.js.api import ConsumerConfig, StreamConfig, StreamInfo
from nats.js.errors import NotFoundError


def make_durable(consumer_config: ConsumerConfig) -> ConsumerConfig:
    if consumer_config.name is None:
        raise ValueError("name of a consumer must be set")
    consumer_config.durable_name = consumer_config.name
    return consumer_config


async def add_or_update_stream(jsm: JetStreamManager, stream_config: StreamConfig) -> StreamInfo:
    try:
        return await jsm.update_stream(stream_config)
    except NotFoundError:
        return await jsm.add_stream(stream_config)
