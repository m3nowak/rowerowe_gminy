import asyncio

import click
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig

from .app import app_factory
from .config import Config
from .register_sub import register_sub


async def gthr(to_gather):
    await asyncio.gather(*to_gather)


@click.command(help="Run server")
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), help="Config file path", required=True)
@click.option("--debug", is_flag=True, help="Debug mode")
@click.option("--no-register", is_flag=True, help="Skip webhook registration")
@click.option("--port", help="Server port", default=8000, type=int)
def run(config_path: str, port: int, debug: bool = False, no_register: bool = False):
    config = Config.from_file(config_path)
    app = app_factory(config, debug_mode=debug)
    hc_config = HypercornConfig()
    hc_config.bind = [f"0.0.0.0:{port}"]
    to_gather = [serve(app, hc_config, mode="asgi")]  # type: ignore
    if not no_register:
        to_gather.append(register_sub(config))
    asyncio.run(gthr(to_gather))
    # uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    run()


if __name__ == "__main__":
    main()
