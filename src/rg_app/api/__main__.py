import click
import uvicorn

from .app import app_factory
from .config import Config

ENV_KEY = "API_WORKER_CFG"
DEFAULT_CFG = "config.api_worker.yaml"


@click.command()
@click.option("-c", "--config", "cfg_path", type=str, help="Path to configuration file", required=True)
@click.option("-d", "--debug", "debug", is_flag=True, help="Enable debug mode", required=False, default=False)
def start(cfg_path: str, debug: bool):
    if debug:
        print("Debug mode")
        from .app_debug import get_debug_config

        config = get_debug_config()

        uvicorn.run(
            "rg_app.api_worker.app_debug:debug_app_factory",
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


def main():
    start()


if __name__ == "__main__":
    main()
