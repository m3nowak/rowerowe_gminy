import asyncio
import json

import aiofiles
import duckdb
import geojson
import polyline
from faststream import Depends
from faststream.nats import NatsRouter
from opentelemetry import trace

from rg_app.common.faststream.otel import tracer_fn
from rg_app.common.internal.geo_svc import (
    GeoSvcCheckPolylineRequest,
    GeoSvcCheckRequest,
    GeoSvcCheckResponse,
    GeoSvcCheckResponseItem,
)
from rg_app.worker.common import DEFAULT_QUEUE
from rg_app.worker.duck_deps import duck_conn

geo_svc_router = NatsRouter("rg.svc.geo.")


@geo_svc_router.subscriber("check-polyline", DEFAULT_QUEUE)
async def check_polyline(
    body: GeoSvcCheckPolylineRequest,
    conn: duckdb.DuckDBPyConnection = Depends(duck_conn),
    tracer: trace.Tracer = Depends(tracer_fn),
) -> GeoSvcCheckResponse:
    geojson_list = polyline.decode(body.data, precision=5, geojson=True)
    line_string = geojson.LineString(geojson_list)
    return await _check(line_string, conn, tracer)


@geo_svc_router.subscriber("check", DEFAULT_QUEUE)
async def check(
    body: GeoSvcCheckRequest,
    conn: duckdb.DuckDBPyConnection = Depends(duck_conn),
    tracer: trace.Tracer = Depends(tracer_fn),
) -> GeoSvcCheckResponse:
    line_string = geojson.LineString(body.coordinates)
    return await _check(line_string, conn, tracer)


def run_query(conn: duckdb.DuckDBPyConnection, filename: str) -> list[tuple[str, str]]:
    return conn.execute(
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
        [filename],
    ).fetchall()


async def _aio_run_query(conn: duckdb.DuckDBPyConnection, filename: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_query, conn, filename)


async def _check(
    line_string: geojson.LineString,
    conn: duckdb.DuckDBPyConnection,
    tracer: trace.Tracer,
) -> GeoSvcCheckResponse:
    async with aiofiles.tempfile.NamedTemporaryFile("wb", suffix=".json") as ntf:
        await ntf.write(json.dumps(line_string).encode("utf-8"))
        with tracer.start_as_current_span("geo_svc_check") as span:
            filename = str(ntf.name)
            result = await _aio_run_query(conn, filename)
            span.set_attribute("result_count", len(result))
            span.set_status(trace.Status(trace.StatusCode.OK))

    resp = GeoSvcCheckResponse(items=[GeoSvcCheckResponseItem(id=row[0], type=row[1]) for row in result])  # type: ignore
    trace.get_current_span().set_status(trace.Status(trace.StatusCode.OK))

    return resp
