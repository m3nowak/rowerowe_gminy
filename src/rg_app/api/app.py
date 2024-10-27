from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.plugins.problem_details import ProblemDetailsConfig, ProblemDetailsPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar.stores.memory import MemoryStore

from rg_app.common.litestar.plugins import ConfigPlugin, NatsPlugin, NatsPluginConfig, StravaPlugin, StravaPluginConfig
from rg_app.common.litestar.plugins.async_exit_stack_plugin import AsyncExitStackPlugin

from .auth import authenticate_handler
from .config import Config
from .internals import hc_handler, rate_limits_handler
from .jwt import SimpleJwtPlugin


def app_factory(config: Config, debug_mode: bool = False) -> Litestar:
    cors_config = CORSConfig(allow_origins=[config.frontend_url.strip("/")])
    sa_config = SQLAlchemyAsyncConfig(connection_string=config.db.get_url())
    sa_plugin = SQLAlchemyInitPlugin(config=sa_config)
    problem_details_plugin = ProblemDetailsPlugin(ProblemDetailsConfig())
    config_plugin = ConfigPlugin(config)

    strava_plugin_config = StravaPluginConfig(
        client_id=config.strava_client_id,
        client_secret=config.get_strava_client_secret(),
    )
    strava_plugin = StravaPlugin(strava_plugin_config)

    nats_plugin_config = NatsPluginConfig(
        url=config.nats.url,
        js=True,
        user_credentials=config.nats.creds_path,
        inbox_prefix=config.nats.inbox_prefix.encode(),
    )
    nats_plugin = NatsPlugin(nats_plugin_config)

    jwt_plugin = SimpleJwtPlugin(
        secret=config.get_jwt_secret(),
        exclude=["/authenticate", "/docs", "/hc", "/rate-limits"],
        token_url=config.login_url,
    )

    aes_plugin = AsyncExitStackPlugin()

    app = Litestar(
        debug=debug_mode,
        route_handlers=[authenticate_handler, hc_handler, rate_limits_handler],
        openapi_config=OpenAPIConfig(
            title="Rowerowe Gminy API",
            version="0.0.1",
            render_plugins=[SwaggerRenderPlugin()],
            path="/docs",
        ),
        stores={"memory": MemoryStore()},
        plugins=[problem_details_plugin, config_plugin, sa_plugin, jwt_plugin, strava_plugin, nats_plugin, aes_plugin],
        cors_config=cors_config,
    )
    return app
