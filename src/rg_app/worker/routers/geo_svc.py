import json
from typing import Any

import aiofiles
import duckdb
from faststream import Depends
from faststream.nats import NatsRouter
from opentelemetry import trace

from rg_app.common.faststream.otel import tracer_fn
from rg_app.common.internal.geo_svc import GeoSvcCheckRequest, GeoSvcCheckResponse, GeoSvcCheckResponseItem
from rg_app.worker.duck_deps import duck_conn

geo_svc_router = NatsRouter("rg.svc.geo.")


@geo_svc_router.subscriber("ping")
async def ping(
    body: dict[str, Any],
) -> str:
    print("Got ping: ", body)
    return "pong"


@geo_svc_router.subscriber("check")
async def check(
    body: GeoSvcCheckRequest,
    conn: duckdb.DuckDBPyConnection = Depends(duck_conn),
    tracer: trace.Tracer = Depends(tracer_fn),
) -> GeoSvcCheckResponse:
    async with aiofiles.tempfile.NamedTemporaryFile("wb", suffix=".json") as ntf:
        await ntf.write(json.dumps(body).encode("utf-8"))
        with tracer.start_as_current_span("geo_svc_check") as span:
            result = conn.execute(
                """
                WITH shp as (
                    SELECT
                    geom
                    FROM ST_Read(?)
                )
                SELECT borders.ID, borders.type
                FROM borders
                INNER JOIN shp ON ST_Intersects(shape, geom)
                """,
                [ntf.name],
            ).fetchall()
            span.set_attribute("result_count", len(result))
            span.set_status(trace.Status(trace.StatusCode.OK, "Query executed"))

    resp = GeoSvcCheckResponse(items=[GeoSvcCheckResponseItem(id=row[0], type=row[1]) for row in result])
    trace.get_current_span().set_status(trace.Status(trace.StatusCode.OK, "Response generated"))

    return resp


# @geo_svc_router.subscriber("recalc")
# async def recalc(
#     broker: NatsBroker,
#     nats_msg: NatsMessage,
#     otel_logger: Logger = Depends(otel_logger),
# ) -> str:
#     print("Got recalc command!")
#     ctx = {}
#     inject(ctx)
#     asyncio.create_task(recalc_border_data(broker, ctx))
#     return "Will recalculate border data"


# async def recalc_border_data(broker: NatsBroker, trace_ctx: dict) -> None:
#     tracer = get_tracer(__name__)
#     with tracer.start_as_current_span("recalc_border_data"):
#         trace_ctx = {}
#         inject(trace_ctx)
#         print("Recalculating border data...")
#         from rg_app.geo.duck_source import aio_create_db

#         conn = await aio_create_db()
#         assert aio_create_db is not None
#         print("Border data recalculated!")
#         # TODO: Do something with the data
