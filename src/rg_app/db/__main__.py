import click

from rg_app.db.manage import migrate as manage_migrate


@click.group()
def cli():
    pass


@cli.command(help="Perform DB migrations", name="migrate")
@click.argument("url")
def migrate(url: str):
    manage_migrate(url)


def main():
    cli()


if __name__ == "__main__":
    cli()
