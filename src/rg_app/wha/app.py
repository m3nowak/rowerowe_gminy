import msgspec
from litestar import Litestar, get, post
from litestar.exceptions import PermissionDeniedException
from litestar.params import Parameter
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.errors import KeyNotFoundError
from typing_extensions import Annotated

from rg_app.common.litestar.plugins import ConfigPlugin, NatsPlugin, NatsPluginConfig

from .common import LOCAL_WH_URL
from .config import Config
from .models import StravaEvent

STRAVA_SUB_URL = "https://www.strava.com/api/v3/push_subscriptions"


@get(f"/{LOCAL_WH_URL}")
async def webhook_validation(
    verify_token: Annotated[str, Parameter(query="hub.verify_token")],
    _: Annotated[str, Parameter(query="hub.mode")],
    challenge: Annotated[str, Parameter(query="hub.challenge")],
    config: Config,
) -> dict[str, str]:
    if verify_token != config.verify_token:
        raise PermissionDeniedException("Invalid verify token")
    return {"hub.challenge": challenge}


@post(f"/{LOCAL_WH_URL}", status_code=202)
async def webhook_handler(
    data: StravaEvent,
    nats: NatsClient,
    config: Config,
) -> dict[str, str]:
    headers = {
        "Nats-Expected-Stream": config.nats.stream,
    }
    topic = ".".join([config.nats.subject_prefix, data.object_type, data.aspect_type])
    await nats.publish(topic, msgspec.json.encode(data), headers=headers)
    return {"status": "ok"}


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


def app_factory(config: Config, debug_mode: bool = False) -> Litestar:
    nats_plugin = NatsPlugin(NatsPluginConfig(url=config.nats.url, js=True))
    config_plugin = ConfigPlugin(config)
    app = Litestar(
        [index, webhook_validation, webhook_handler],
        plugins=[nats_plugin, config_plugin],
        debug=debug_mode,
    )

    return app
