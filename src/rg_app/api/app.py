from litestar import Litestar
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.plugins.problem_details import ProblemDetailsConfig, ProblemDetailsPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin

from rg_app.api.auth import authenticate_handler, jwt_auth
from rg_app.api.config import Config
from rg_app.api.plugins.config_plugin import ConfigPlugin


def app_factory(config: Config, debug_mode: bool = False) -> Litestar:
    sa_config = SQLAlchemyAsyncConfig(connection_string=config.db_url)
    sa_plugin = SQLAlchemyInitPlugin(config=sa_config)
    problem_details_plugin = ProblemDetailsPlugin(ProblemDetailsConfig())
    config_plugin = ConfigPlugin(config)
    app = Litestar(
        debug=debug_mode,
        route_handlers=[authenticate_handler],
        openapi_config=OpenAPIConfig(
            title="Rowerowe Gminy API",
            version="0.0.1",
            render_plugins=[SwaggerRenderPlugin()],
            path="/docs",
        ),
        on_app_init=[jwt_auth.on_app_init],
        plugins=[problem_details_plugin, config_plugin, sa_plugin],
    )
    return app
