from faststream import Path
from faststream.nats import NatsRouter

from rg_app.worker.common import DEFAULT_QUEUE

echo_router = NatsRouter("echo.")


@echo_router.subscriber("{subpath}", DEFAULT_QUEUE)
async def hi(body: str, subpath: str = Path()) -> str:
    return f"hello on {subpath}:\n{body}"
