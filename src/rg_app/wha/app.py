from litestar import Litestar, get, post
from litestar.exceptions import PermissionDeniedException, ServiceUnavailableException
from litestar.params import Parameter
from nats.js import JetStreamContext
from typing_extensions import Annotated

from rg_app.common.litestar.plugins import AsyncExitStackPlugin, ConfigPlugin, NatsPlugin, NatsPluginConfig
from rg_app.common.litestar.plugins.nats import JetStreamPlugin
from rg_app.common.strava.models.webhook import WebhookUnion
from rg_app.nats_util.client import NatsClient

from .common import LOCAL_WH_URL
from .config import Config

# from .models import StravaEvent
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
async def webhook_handler(path_token: str, data: WebhookUnion, js: JetStreamContext, config: Config) -> dict[str, str]:
    if path_token != config.get_verify_token():
        raise PermissionDeniedException("Invalid path token")
    data_root = data.root
    topic = ".".join(
        [config.nats.subject_prefix, data_root.object_type, str(data_root.owner_id), str(data_root.object_id)]
    )
    await js.publish(topic, data_root.model_dump_json().encode(), stream=config.nats.stream)
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
            user_credentials=config.nats.creds_path,
            inbox_prefix=config.nats.inbox_prefix.encode(),
        )
    )
    config_plugin = ConfigPlugin(config)
    on_startup = []
    if not no_register:
        on_startup.append(register_sub_hook_factory(config, 5))
    else:
        print("Skipping webhook registration")
        print(f"Webhook URL path: /{LOCAL_WH_URL}/{config.get_verify_token()}")

    app = Litestar(
        [index, webhook_validation, webhook_handler],
        plugins=[nats_plugin, config_plugin, AsyncExitStackPlugin(), JetStreamPlugin(config.nats.js_domain)],
        debug=debug_mode,
        on_startup=on_startup,
    )

    return app
