import asyncio

import click
import uvicorn

from .app import app_factory
from .config import Config


async def gthr(to_gather):
    await asyncio.gather(*to_gather)


@click.command(help="Run server")
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), help="Config file path", required=True)
@click.option("--debug", is_flag=True, help="Debug mode")
@click.option("", is_flag=True, help="Skip webhook registration")
@click.option("--port", help="Server port", default=8000, type=int)
def run(config_path: str, port: int, debug: bool = False, no_register: bool = False):
    config = Config.from_file(config_path)
    app = app_factory(config, debug_mode=debug, no_register=no_register)
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    run()


if __name__ == "__main__":
    main()
