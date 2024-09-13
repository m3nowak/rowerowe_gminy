from litestar import Litestar, get
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.errors import KeyNotFoundError

from rg_app.common.litestar.plugins import NatsPlugin, NatsPluginConfig


@get("/")
async def index(nats: NatsClient, js: JetStreamContext) -> str:
    hello = "Hello, world!"
    await nats.publish("hello", hello.encode())
    kv = await js.key_value("hello")
    try:
        entry = await kv.get("hello")
        current_val = int(entry.value.decode() if entry.value else 0)
    except KeyNotFoundError:
        current_val = 0
    await kv.put("hello", str(current_val + 1).encode())
    return f"Hello, world!, {current_val}"


nats_plugin = NatsPlugin(NatsPluginConfig(url="nats://localhost:4222", js=True))

app = Litestar([index], plugins=[nats_plugin], debug=True)
