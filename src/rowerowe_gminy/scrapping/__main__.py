import click

import rowerowe_gminy.scrapping

from .adm_info import save_data


@click.group()
def cli():
    pass


@cli.command(help="Download data about administrative units")
@click.option(
    "--output",
    "-o",
    default=".",
    help="Output directory",
    type=click.Path(exists=True, file_okay=False, writable=True),
    required=True,
)
def adm(output: str):
    save_data(output)


def main():
    cli()


if __name__ == "__main__":
    main()
