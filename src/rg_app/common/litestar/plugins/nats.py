from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

import nats
from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext


@dataclass
class NatsPluginConfig:
    """Configuration for the NatsPlugin
    Args:
    ----------
    url: str | list[str]
        URL(s) of the NATS server(s)
    js: bool | list[str] = False
        If True, JetStream will be enabled, if list of strings, will enable JetStream with the provided domains
    nats_kwarg: str = "nats"
        Name of the key in the DI container for the NATS client
    js_kwarg: str = "js"
        Name of the key in the DI container for the JetStream client
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
    js: bool | list[str] = False
    nats_kwarg: str = "nats"
    js_kwarg: str = "js"
    user_credentials: str | None = None
    inbox_prefix: bytes | None = b"_INBOX"
    user: str | None = None
    password: str | None = None
    token: str | None = None
    conn_kwargs: dict[str, str] | None = None


_STATE_KEY = "nats"


class NatsPlugin(InitPluginProtocol):
    """NATS plugin for Litestar"""

    def __init__(self, np_cfg: NatsPluginConfig) -> None:
        super().__init__()
        self.cfg = np_cfg

    def context_manager_factory(self):
        @asynccontextmanager
        async def nats_ctx(app: Litestar) -> AsyncGenerator[None, None]:
            try:
                nc = app.state[_STATE_KEY]
            except KeyError:
                conn_kwargs = self.cfg.conn_kwargs or {}
                nc = await nats.connect(
                    self.cfg.url,
                    user_credentials=self.cfg.user_credentials,
                    inbox_prefix=self.cfg.inbox_prefix,
                    user=self.cfg.user,
                    password=self.cfg.password,
                    token=self.cfg.token,
                    **conn_kwargs,
                )
                app.state[_STATE_KEY] = nc
            try:
                yield
            finally:
                await nc.close()

        return nats_ctx

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.lifespan.append(self.context_manager_factory())

        def nats_provide_fn() -> NatsClient:
            return app_config.state[_STATE_KEY]

        def jetstream_provide_fn(domain: str | None = None) -> JetStreamContext:
            return app_config.state[_STATE_KEY].jetstream(domain=domain)

        app_config.dependencies[self.cfg.nats_kwarg] = Provide(nats_provide_fn, sync_to_thread=False)
        if self.cfg.js:
            app_config.dependencies[self.cfg.js_kwarg] = Provide(lambda: jetstream_provide_fn(), sync_to_thread=False)
            if isinstance(self.cfg.js, list):
                for domain in self.cfg.js:
                    domain_kwarg = f"{self.cfg.js_kwarg}_{domain}"
                    app_config.dependencies[domain_kwarg] = Provide(
                        lambda: jetstream_provide_fn(domain), sync_to_thread=False
                    )
        return app_config
