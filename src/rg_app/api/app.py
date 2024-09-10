from litestar import Litestar
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.plugins.problem_details import ProblemDetailsConfig, ProblemDetailsPlugin

from rg_app.api.auth import authenticate_handler, jwt_auth

from rg_app.api.plugins.config_plugin import ConfigPlugin
from rg_app.api.config import Config

def app_factory(config: Config) -> Litestar:
    problem_details_plugin = ProblemDetailsPlugin(ProblemDetailsConfig())
    config_plugin = ConfigPlugin(config)
    app = Litestar(
        route_handlers=[authenticate_handler],
        openapi_config=OpenAPIConfig(
            title="Rowerowe Gminy API",
            version="0.0.1",
            render_plugins=[SwaggerRenderPlugin()],
            path="/docs",
        ),
        on_app_init=[jwt_auth.on_app_init],
        plugins=[problem_details_plugin],
    )
    return app
