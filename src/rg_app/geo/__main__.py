import os

import click

from .duck_export import pg_export
from .duck_source import create_db
from .preprocessing import preprocess_gml

ENV_PG_CONN = "PG_CONN"


@click.group()
def cli():
    pass


@cli.command(help="Generate simplified topology in topojson format", name="mktopo")
@click.option("--db_path", help="Path to the DuckDB database file", required=True)
@click.option("--tolerance", help="Simplification tolerance", default=0.005)
@click.option("--output", help="Output path", default="topo.json")
def cmd_mktopo(db_path: str, tolerance: float, output: str):
    click.echo(f"Generating simplified topology in topojson format with tolerance {tolerance}")
    from .simplification import toposimplify_duckdb

    topojson = toposimplify_duckdb(db_path, tolerance)
    with open(output, "w") as f:
        f.write(topojson)
    click.echo(f"Saved to {output}")


@cli.command(help="Create DuckDB database", name="create-ddb")
@click.option("--json_dir", help="Path to the directory with JSON files", default=None)
@click.option("--db_path", help="Path to the DuckDB database file", default=None)
def cmd_create_db(json_dir: str | None = None, db_path: str | None = None):
    print("Creating DuckDB database")
    create_db(json_dir, db_path)
    click.echo("Database created")


@cli.command(help="Preprocess GML file to geojson", name="preprocess")
@click.option("--path", help="Path to the dir with GML files", required=True)
def cmd_preprocess(path: str):
    print(f"Preprocessing {path}")
    preprocess_gml(path)
    click.echo("Preprocessing complete")


@cli.command(help="Perform DB migrations", name="pg-export")
@click.option(
    "--pg_conn",
    help="Postgres connection string like 'dbname=postgres host=localhost user=postgres password=postgres'",
    default=None,
)
@click.option("--db_path", help="Path to the DuckDB database file", default=None)
def cmd_pg_export(pg_conn: str | None, db_path: str | None = None):
    click.echo("Exporting DuckDB regions to Postgres")
    pg_conn = pg_conn or os.getenv(ENV_PG_CONN)
    if not pg_conn:
        click.echo(f"Missing required argument --pg_conn or environment variable {ENV_PG_CONN}", err=True)
        exit(1)

    pg_export(pg_conn, db_path)
    click.echo("Export complete")


def main():
    cli()


if __name__ == "__main__":
    cli()
