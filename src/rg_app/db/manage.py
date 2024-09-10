import os

import alembic.command
import alembic.config
from sqlalchemy import MetaData

import rg_app.db.models

_SCHEME = "postgresql+psycopg"


def generate_url(
    username: str, password: str, dbname: str = "postgres", host: str = "localhost", port: str = "5432"
) -> str:
    return f"{_SCHEME}://{username}:{password}@{host}:{port}/{dbname}"


def migrate(db_url: str):
    pkg_path = os.path.dirname(rg_app.db.__file__)

    alembic_cfg = alembic.config.Config(os.path.join(pkg_path, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", os.path.join(pkg_path, "alembic"))
    alembic.command.upgrade(alembic_cfg, "head")


def obtain_metadata() -> MetaData:
    from rg_app.db.models import Base

    # this import is necessary to register the models
    return Base.metadata
