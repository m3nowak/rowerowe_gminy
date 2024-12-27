import click

from .duck_export import pg_export
from .duck_source import create_db
from .preprocessing import preprocess_gml


@click.group()
def cli():
    pass


@cli.command(help="Generate simplified topology in topojson format", name="mktopo")
@click.option("--duckdb_path", help="Path to the DuckDB database file", required=True)
@click.option("--tolerance", help="Simplification tolerance", default=0.005)
def cmd_mktopo(duckdb_path: str, tolerance: float):
    click.echo(f"Generating simplified topology in topojson format with tolerance {tolerance}")
    from .simplification import toposimplify_duckdb

    topojson = toposimplify_duckdb(duckdb_path, tolerance)
    filename = "tpy{:.0e}.json".format(tolerance).replace("-", "_")
    with open(filename, "w") as f:
        f.write(topojson)
    click.echo(f"Saved to {filename}")


@cli.command(help="Create DuckDB database", name="create-db")
@click.option("--json_dir", help="Path to the directory with JSON files", default=None)
@click.option("--db_path", help="Path to the DuckDB database file", default=None)
def cmd_create_db(json_dir: str | None = None, db_path: str | None = None):
    print("Creating DuckDB database")
    create_db(json_dir, db_path)


@cli.command(help="Preprocess GML file to geojson", name="preprocess")
@click.option("--path", help="Path to the GML file", required=True)
def cmd_preprocess(path: str):
    print(f"Preprocessing {path}")
    preprocess_gml(path)


@cli.command(help="Perform DB migrations", name="pg-export")
@click.option(
    "--pg_conn",
    help="Postgres connection string like 'dbname=postgres host=localhost user=postgres password=postgres'",
    required=True,
)
@click.option("--duckdb_path", help="Path to the DuckDB database file", default=None)
def cmd_pg_export(pg_conn: str, duckdb_path: str | None = None):
    print("Exporting DuckDB regions to Postgres")
    pg_export(pg_conn, duckdb_path)


def main():
    cli()


if __name__ == "__main__":
    cli()
