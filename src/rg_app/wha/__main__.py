
import click
import uvicorn

from .app import app



@click.command(help="Run server")
# @click.option("-c", "--config", "config_path", type=click.Path(exists=True), help="Config file path", required=True)
@click.option("--debug", is_flag=True, help="Debug mode")
def run(debug: bool = False):
    # config = Config.from_file(config_path)
    # app = app_factory(config, debug_mode=debug)
    uvicorn.run(app, host="0.0.0.0", port=8000)

def main():
    run()


if __name__ == "__main__":
    main()
