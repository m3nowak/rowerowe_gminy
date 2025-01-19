import os

import click

from rg_app.db.manage import migrate as manage_migrate

RG_DB_URL_ENV = "RG_DB_URL"


@click.group()
def cli():
    pass


@cli.command(help="Perform DB migrations", name="migrate")
@click.option("--url")
def migrate(url: str | None):
    url = url or os.getenv(RG_DB_URL_ENV)
    if url is None:
        click.echo(f"Please provide DB URL via --url or {RG_DB_URL_ENV} environment variable")
        exit(1)
    manage_migrate(url)


def main():
    cli()


if __name__ == "__main__":
    cli()
