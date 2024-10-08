import msgspec
from litestar import Litestar, get, post
from litestar.exceptions import PermissionDeniedException, ServiceUnavailableException
from litestar.params import Parameter
from nats.js import JetStreamContext
from typing_extensions import Annotated

from rg_app.common.litestar.plugins import ConfigPlugin, NatsPlugin, NatsPluginConfig
from rg_app.nats_util.client import NatsClient

from .common import LOCAL_WH_URL
from .config import Config
from .models import StravaEvent
from .register_sub import register_sub_hook_factory


@get(f"/{LOCAL_WH_URL}/{{path_token:str}}")
async def webhook_validation(
    path_token: str,
    verify_token: Annotated[str, Parameter(query="hub.verify_token", default="")],
    _: Annotated[str, Parameter(query="hub.mode", default="")],
    challenge: Annotated[str, Parameter(query="hub.challenge", default="")],
    config: Config,
) -> dict[str, str]:
    if verify_token != config.get_verify_token():
        raise PermissionDeniedException("Invalid verify token")
    if path_token != config.get_verify_token():
        raise PermissionDeniedException("Invalid path token")
    print("Webhook validation successful")
    return {"hub.challenge": challenge}


@post(f"/{LOCAL_WH_URL}/{{path_token:str}}", status_code=200)
async def webhook_handler(path_token: str, data: StravaEvent, js: JetStreamContext, config: Config) -> dict[str, str]:
    if path_token != config.get_verify_token():
        raise PermissionDeniedException("Invalid path token")
    topic = ".".join([config.nats.subject_prefix, data.object_type, str(data.object_id)])
    await js.publish(topic, msgspec.json.encode(data), stream=config.nats.stream)
    return {"status": "ok"}


@get("/")
async def index(nats: NatsClient) -> str:
    if nats.is_connected:
        return "Server ready"
    else:
        raise ServiceUnavailableException("NATS connection is not ready")


def app_factory(config: Config, debug_mode: bool = False, no_register: bool = False) -> Litestar:
    nats_plugin = NatsPlugin(
        NatsPluginConfig(
            url=config.nats.url,
            js=True,
            user_credentials=config.nats.creds_path,
            inbox_prefix=config.nats.inbox_prefix.encode(),
        )
    )
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
