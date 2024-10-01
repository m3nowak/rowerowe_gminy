import typing as ty

from nats.js import JetStreamManager
from nats.js.api import AckPolicy, ConsumerConfig, StreamConfig

from .utils import add_or_update_stream, make_durable

STREAM_INCOMING_WHA = StreamConfig(
    name="incoming-wha",
    description="Strava incoming webhooks",
    subjects=["rg.wha.*.*"],
    max_msgs_per_subject=1,
    max_bytes=1 * (1024**3),  # 1GB
)

CONSUMER_ACTIVITIES = make_durable(
    ConsumerConfig(
        "activities",
        description="Process incoming activities",
        ack_policy=AckPolicy.ALL,
        filter_subject="rg.wha.activitiy.*",
        deliver_subject="rg.consumer.activities",
    )
)

CONSUMER_REVOCATIONS = make_durable(
    ConsumerConfig(
        "revocations",
        description="Process incoming revocations",
        ack_policy=AckPolicy.ALL,
        filter_subject="rg.wha.athlete.*",
        deliver_subject="rg.consumer.revocations",
    )
)


async def setup(jsm: JetStreamManager):
    await add_or_update_stream(jsm, STREAM_INCOMING_WHA)
    await jsm.add_consumer(ty.cast(str, STREAM_INCOMING_WHA.name), CONSUMER_ACTIVITIES)
    await jsm.add_consumer(ty.cast(str, STREAM_INCOMING_WHA.name), CONSUMER_REVOCATIONS)
