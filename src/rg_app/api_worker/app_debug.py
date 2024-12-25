import os

from .config import Config

ENV_KEY = "API_WORKER_CFG"
DEFAULT_CFG = "config.api_worker.yaml"


def get_debug_config():
    print(f"Debug mode, using config ftom env ({ENV_KEY}) or default ({DEFAULT_CFG})")
    cfg_path = os.environ.get(ENV_KEY, DEFAULT_CFG)
    return Config.from_file(cfg_path)
