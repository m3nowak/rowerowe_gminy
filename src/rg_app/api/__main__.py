import json

import click
import uvicorn
import yaml

from rg_app.api import Config, app_factory


@click.group()
def cli():
    pass


@cli.command(help="Run server", name="run")
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), help="Config file path", required=True)
@click.option("--debug", is_flag=True, help="Debug mode")
@click.option("--port", help="Server port", default=8000, type=int)
def run(config_path: str, port: int, debug: bool = False):
    config = Config.from_file(config_path)
    app = app_factory(config, debug_mode=debug)
    uvicorn.run(app, host="0.0.0.0", port=port)


@cli.command(help="Generate OpenAPI schema", name="openapi")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("-j/-y", "--json/--yaml", "is_json", default=True, help="Output format")
def openapi(output: str | None, is_json: bool):
    app = app_factory(Config.dummy())
    openapi_data = app.openapi_schema.to_schema()
    if is_json:
        openapi_text = json.dumps(openapi_data, indent=2)
    else:
        openapi_text = yaml.dump(openapi_data)

    if output:
        with open(output, "w") as f:
            f.write(openapi_text)
    else:
        click.echo(openapi_text)


def main():
    cli()


if __name__ == "__main__":
    cli()
