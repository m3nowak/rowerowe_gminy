from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol

STATE_KEY = "async_exit_stack"


class AsyncExitStackPlugin(InitPluginProtocol):
    """AsyncExitStack plugin for Litestar"""

    def __init__(self) -> None:
        super().__init__()
        self.exit_stack = AsyncExitStack()

    def context_manager_factory(self):
        @asynccontextmanager
        async def exit_stack_ctx(app: Litestar) -> AsyncGenerator[None, None]:
            async with self.exit_stack as stack:
                if STATE_KEY not in app.state or app.state[STATE_KEY] is None:
                    app.state[STATE_KEY] = stack
                try:
                    yield
                finally:
                    pass

        return exit_stack_ctx

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.lifespan.append(self.context_manager_factory())

        def provide_exit_stack() -> AsyncExitStack:
            return app_config.state[STATE_KEY]

        app_config.dependencies[STATE_KEY] = Provide(provide_exit_stack, sync_to_thread=False)

        return app_config
