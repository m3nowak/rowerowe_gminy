import msgspec
from litestar import Litestar, get, post
from litestar.exceptions import PermissionDeniedException, ServiceUnavailableException
from litestar.params import Parameter
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.errors import KeyNotFoundError
from typing_extensions import Annotated

from rg_app.common.litestar.plugins import ConfigPlugin, NatsPlugin, NatsPluginConfig

from .common import LOCAL_WH_URL
from .config import Config
from .models import StravaEvent
from .register_sub import register_sub_hook_factory


@get(f"/{LOCAL_WH_URL}")
async def webhook_validation(
    verify_token: Annotated[str, Parameter(query="hub.verify_token", default="")],
    _: Annotated[str, Parameter(query="hub.mode", default="")],
    challenge: Annotated[str, Parameter(query="hub.challenge", default="")],
    config: Config,
) -> dict[str, str]:
    if verify_token != config.verify_token:
        raise PermissionDeniedException("Invalid verify token")
    return {"hub.challenge": challenge}


@post(f"/{LOCAL_WH_URL}", status_code=202)
async def webhook_handler(
    data: StravaEvent,
    nats: NatsClient,
    js: JetStreamContext,
    config: Config,
) -> dict[str, str]:
    topic = ".".join([config.nats.subject_prefix, data.object_type, data.aspect_type])
    await js.publish(topic, msgspec.json.encode(data), stream=config.nats.stream)
    return {"status": "ok"}


@get("/")
async def index(nats: NatsClient, js: JetStreamContext) -> str:
    if nats.is_connected:
        return "Server ready"
    else:
        raise ServiceUnavailableException("NATS connection is not ready")


def app_factory(config: Config, debug_mode: bool = False, no_register: bool = False) -> Litestar:
    nats_plugin = NatsPlugin(NatsPluginConfig(url=config.nats.url, js=True, user_credentials=config.nats.creds_path))
    config_plugin = ConfigPlugin(config)
    on_startup = []
    if not no_register:
        on_startup.append(register_sub_hook_factory(config, 5))

    app = Litestar(
        [index, webhook_validation, webhook_handler],
        plugins=[nats_plugin, config_plugin],
        debug=debug_mode,
        on_startup=on_startup,
    )

    return app
