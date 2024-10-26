from nats.js import JetStreamContext
from nats.js.api import StreamConfig

from .utils import add_or_update_stream

STREAM_INCOMING_WHA = StreamConfig(
    name="incoming-wha",
    description="Strava incoming webhooks",
    subjects=["rg.incoming.wha.*.*"],
    max_msgs_per_subject=1,
    max_bytes=1 * (1024**3),  # 1GB
)


async def setup(js: JetStreamContext):
    jsm = js._jsm
    await add_or_update_stream(jsm, STREAM_INCOMING_WHA)
