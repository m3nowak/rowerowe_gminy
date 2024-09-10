import json

import click
import uvicorn
import yaml

from rg_app.api.app import app_factory


@click.group()
def cli():
    pass


@cli.command(help="Run server", name="run")
def run():
    app = app_factory()
    uvicorn.run(app, host="0.0.0.0", port=8000)


@cli.command(help="Generate OpenAPI schema", name="openapi")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("-j/-y", "--json/--yaml", "is_json", default=True, help="Output format")
def openapi(output: str | None, is_json: bool):
    app = app_factory()
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
