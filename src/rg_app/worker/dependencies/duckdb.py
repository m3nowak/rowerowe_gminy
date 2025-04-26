from contextlib import asynccontextmanager
from typing import Annotated

import duckdb
from faststream import ContextRepo, Depends

DUCKDB_REPO_KEY = "duck_conn"


def lifespan_factory(db_path: str):
    @asynccontextmanager
    async def lifespan(context: ContextRepo):
        with duckdb.connect(db_path, read_only=True) as conn:
            conn.install_extension("spatial")
            conn.load_extension("spatial")
            context.set_global(DUCKDB_REPO_KEY, conn)
            yield

    return lifespan


async def duck_conn(context: ContextRepo) -> duckdb.DuckDBPyConnection:
    conn = context.get(DUCKDB_REPO_KEY)
    return conn


DuckDBConnDI = Annotated[duckdb.DuckDBPyConnection, Depends(duck_conn)]
