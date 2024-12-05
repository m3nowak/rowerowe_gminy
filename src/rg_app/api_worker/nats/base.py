from rg_app.api_worker.config import NatsConfig
from rg_app.api_worker.dependencies.config import Config

from .common import DEFAULT_QUEUE
from .stateful_nats_router import StatefulNatsRouter


def router_factory(nats_config: NatsConfig, state):
    router = StatefulNatsRouter(
        nats_config.url,
        inbox_prefix=nats_config.inbox_prefix,
        user_credentials=nats_config.creds_path,
    )
    router.attach_state(state)

    @router.subscriber("hello", DEFAULT_QUEUE)
    async def hello(data: str, config: Config) -> str:
        return f"Hello {data} ({config.tlo})"

    return router
