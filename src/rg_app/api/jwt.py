import typing as ty
from datetime import timedelta

from litestar import Request, Response
from litestar.config.app import AppConfig
from litestar.connection import ASGIConnection
from litestar.datastructures import State
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from litestar.security.jwt import OAuth2PasswordBearerAuth, Token

from rg_app.common.msg import BaseStruct


class MinimalUser(BaseStruct):
    id: int


_STATE_KEY = "jwt_plugin_stuff"


async def _retrieve_user_handler(
    token: Token, connection: "ASGIConnection[ty.Any, ty.Any, ty.Any, ty.Any]"
) -> ty.Optional[MinimalUser]:
    return MinimalUser(id=int(token.sub))


# Ugly hack, somehow JWTAuth cannot be used as a dependency
class CreateTokenHandler:
    def __init__(self, o2a: OAuth2PasswordBearerAuth[MinimalUser]) -> None:
        self.o2a = o2a

    def create_token(
        self,
        identifier: str,
        token_expiration: timedelta | None = None,
        token_issuer: str | None = None,
        token_audience: str | None = None,
        token_unique_jwt_id: str | None = None,
        token_extras: dict | None = None,
        **kwargs: ty.Any,
    ) -> str:
        return self.o2a.create_token(
            identifier, token_expiration, token_issuer, token_audience, token_unique_jwt_id, token_extras, **kwargs
        )

    def create_response(
        self,
        identifier: str,
        token_expiration: timedelta | None = None,
        token_issuer: str | None = None,
        token_audience: str | None = None,
        token_unique_jwt_id: str | None = None,
        token_extras: dict | None = None,
        **kwargs: ty.Any,
    ) -> Response:
        return self.o2a.login(
            identifier=identifier,
            token_expiration=token_expiration,
            token_issuer=token_issuer,
            token_audience=token_audience,
            token_unique_jwt_id=token_unique_jwt_id,
            token_extras=token_extras,
            **kwargs,
        )


class SimpleJwtPlugin(InitPluginProtocol):
    def __init__(self, secret: str, exclude: list[str], token_url: str) -> None:
        self.jwt_auth = OAuth2PasswordBearerAuth[MinimalUser](
            retrieve_user_handler=_retrieve_user_handler,
            token_url=token_url,
            token_secret=secret,
            exclude=exclude,
        )

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        def get_jwt(state: State) -> CreateTokenHandler:
            return state[_STATE_KEY]

        def get_user(request: Request[MinimalUser, Token, ty.Any]) -> MinimalUser:
            return request.user

        def get_token(request: Request[MinimalUser, Token, ty.Any]) -> Token:
            return request.auth

        app_config.state[_STATE_KEY] = CreateTokenHandler(self.jwt_auth)
        app_config.dependencies["o2a"] = Provide(get_jwt, sync_to_thread=False)
        app_config.dependencies["user"] = Provide(get_user, sync_to_thread=False)
        app_config.dependencies["token"] = Provide(get_token, sync_to_thread=False)
        app_config = self.jwt_auth.on_app_init(app_config)
        return app_config
