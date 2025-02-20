from json import dumps

import click
import uvicorn
import yaml

from .app import app_factory
from .config import Config


@click.group()
def cli():
    pass


@cli.command("start")
@click.option("-c", "--config", "cfg_path", type=str, help="Path to configuration file", required=True)
@click.option("-d", "--debug", "debug", is_flag=True, help="Enable debug mode", required=False, default=False)
def start(cfg_path: str, debug: bool):
    if debug:
        print("Debug mode")
        from .app_debug import get_debug_config

        config = get_debug_config()

        uvicorn.run(
            "rg_app.api.app_debug:debug_app_factory",
            host=config.http.host,
            port=config.http.port,
            reload=True,
            factory=True,
        )
    else:
        config = Config.from_file(cfg_path)
        click.echo(f"Starting server on {config.http.host}:{config.http.port}")
        app = app_factory(config)
        uvicorn.run(app, host=config.http.host, port=config.http.port, reload=debug)


@cli.command("openapi")
@click.option("-j", "--json", is_flag=True, help="Output as JSON")
@click.option("-o", "--output", type=str, help="Output file")
@click.option("-c", "--config", "cfg_path", type=str, help="Path to configuration file", required=True)
def openapi(json: bool = False, output: str | None = None, cfg_path: str | None = None):
    config = Config.from_file(cfg_path or "config.yaml")
    app = app_factory(config)
    app.openapi_schema

    if json:
        serialized = dumps(app.openapi())
    else:
        serialized = yaml.safe_dump(app.openapi())

    if output:
        with open(output, "w") as f:
            f.write(serialized)
    else:
        print(serialized)


def main():
    cli()


if __name__ == "__main__":
    main()
