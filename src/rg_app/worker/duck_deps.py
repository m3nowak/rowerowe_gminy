from contextlib import AsyncExitStack

import duckdb
import httpx
from aiofiles.tempfile import NamedTemporaryFile
from faststream import ContextRepo

from .config import Config


async def after_startup(context: ContextRepo):
    config: Config = context.get("config")
    aes: AsyncExitStack = context.get("exit_stack")
    if config.duck_db_path.startswith("http://") or config.duck_db_path.startswith("https://"):
        print(f"Downloading {config.duck_db_path}")
        f = await aes.enter_async_context(NamedTemporaryFile("wb", suffix=".db", delete_on_close=False))
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", config.duck_db_path) as response:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)
        db_path = str(f.name)
        print(f"Downloaded to {db_path}")
        await f.close()
    else:
        db_path = config.duck_db_path
    conn = aes.enter_context(duckdb.connect(db_path, read_only=True))
    conn.load_extension("spatial")
    context.set_global("duck_conn", conn)


async def duck_conn(context: ContextRepo) -> duckdb.DuckDBPyConnection:
    conn = context.get("duck_conn")
    return conn
