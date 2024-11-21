import asyncio
from logging import Logger

from faststream import Depends
from faststream.nats import NatsRouter
from faststream.nats.annotations import NatsBroker, NatsMessage
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import Tracer, get_tracer

from rg_app.common.faststream.otel import otel_logger, tracer_fn

geo_svc_router = NatsRouter("rg.svc.geo.")


@geo_svc_router.subscriber("ping")
async def ping(
    body: str,
    broker: NatsBroker,
    nats_msg: NatsMessage,
    otel_logger: Logger = Depends(otel_logger),
) -> str:
    print("Got ping: ", body)
    return "pong"


@geo_svc_router.subscriber("recalc")
async def recalc(
    broker: NatsBroker,
    nats_msg: NatsMessage,
    otel_logger: Logger = Depends(otel_logger),
) -> str:
    print("Got recalc command!")
    ctx = {}
    inject(ctx)
    asyncio.create_task(recalc_border_data(broker, ctx))
    return "Will recalculate border data"


async def recalc_border_data(broker: NatsBroker, trace_ctx: dict) -> None:
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("recalc_border_data"):
        trace_ctx = {}
        inject(trace_ctx)
        print("Recalculating border data...")
        from rg_app.geo.source_borders import get_gdf

        gdf = await get_gdf()
        assert gdf is not None
        print("Border data recalculated!")
        print(gdf.head())
        # TODO: Do something with the data
