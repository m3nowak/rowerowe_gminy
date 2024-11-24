from contextlib import AsyncExitStack

import duckdb
from faststream import ContextRepo

from .config import Config


async def after_startup(context: ContextRepo):
    config: Config = context.get("config")
    aes: AsyncExitStack = context.get("exit_stack")
    conn = aes.enter_context(duckdb.connect(config.duck_db_path))
    conn.load_extension("spatial")
    context.set_global("duck_conn", conn)


async def duck_conn(context: ContextRepo) -> duckdb.DuckDBPyConnection:
    conn = context.get("duck_conn")
    return conn
