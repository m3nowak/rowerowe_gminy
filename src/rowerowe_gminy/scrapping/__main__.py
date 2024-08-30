import click

import rowerowe_gminy.scrapping

@click.group()
def cli():
    pass

@cli.command(help="Download data about administrative units")
@click.option("--output", "-o", default=".", help="Output directory", type=click.Path(exists=True, file_okay=False, writable=True), required=True)
def adm(output: str):
    rowerowe_gminy.scrapping.save_data(output)

def main():
    cli()

if __name__ == "__main__":
    main()