from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from nats.js import JetStreamContext

from rg_app.nats_util.client import NatsClient
from rg_app.nats_util.client import connect as nats_connect

NATS_STATE_KEY = "nats"


@dataclass
class NatsPluginConfig:
    """Configuration for the NatsPlugin
    Args:
    ----------
    url: str | list[str]
        URL(s) of the NATS server(s)
    nats_kwarg: str = "nats"
        Name of the key in the DI container for the NATS client
    user_credentials: str | None = None
        Path to the user credentials file
    inbox_prefix: bytes | None = b"_INBOX"
        Prefix for the inbox
    username: str | None = None
        Username for the NATS server
    password: str | None = None
        Password for the NATS server
    token: str | None = None
        Token for the NATS server
    conn_kwargs: dict[str, str] | None = None
        Additional keyword arguments to pass to the NATS client
    """

    url: str | list[str]
    nats_kwarg: str = NATS_STATE_KEY
    user_credentials: str | None = None
    inbox_prefix: bytes | None = b"_INBOX"
    user: str | None = None
    password: str | None = None
    token: str | None = None
    conn_kwargs: dict[str, str] | None = None


class JetStreamPlugin(InitPluginProtocol):
    def __init__(self, js_domain: str | None, kwarg: str = "js") -> None:
        self.js_domain = js_domain
        self.kwarg = kwarg

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        def jetstream_provide_fn() -> JetStreamContext:
            if NATS_STATE_KEY in app_config.state:
                return app_config.state[NATS_STATE_KEY].jetstream(domain=self.js_domain)
            else:
                raise ValueError("NATS client not found in app state. Is the NatsPlugin configured?")

        app_config.dependencies[self.kwarg] = Provide(jetstream_provide_fn, sync_to_thread=False)
        return app_config


class NatsPlugin(InitPluginProtocol):
    """NATS plugin for Litestar"""

    def __init__(self, np_cfg: NatsPluginConfig) -> None:
        super().__init__()
        self.cfg = np_cfg

    def context_manager_factory(self):
        @asynccontextmanager
        async def nats_ctx(app: Litestar) -> AsyncGenerator[None, None]:
            try:
                nc = app.state[NATS_STATE_KEY]
            except KeyError:
                conn_kwargs = self.cfg.conn_kwargs or {}
                nc = await nats_connect(
                    self.cfg.url,
                    user_credentials=self.cfg.user_credentials,
                    inbox_prefix=self.cfg.inbox_prefix,
                    user=self.cfg.user,
                    password=self.cfg.password,
                    token=self.cfg.token,
                    **conn_kwargs,
                )
                app.state[NATS_STATE_KEY] = nc
            try:
                yield
            finally:
                await nc.close()

        return nats_ctx

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.lifespan.append(self.context_manager_factory())

        def nats_provide_fn() -> NatsClient:
            return app_config.state[NATS_STATE_KEY]

        app_config.dependencies[self.cfg.nats_kwarg] = Provide(nats_provide_fn, sync_to_thread=False)

        return app_config
