import asyncio

import click

from .app import app_factory
from .config import Config


async def gthr(to_gather):
    await asyncio.gather(*to_gather)


@click.command(help="Run worker")
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), help="Config file path", required=True)
@click.option("--debug", is_flag=True, help="Debug mode")
def run(config_path: str, debug: bool = False):
    config = Config.from_file(config_path)
    app = app_factory(config, debug)

    asyncio.run(app.run())


def main():
    run()


if __name__ == "__main__":
    main()
