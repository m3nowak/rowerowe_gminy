import os
import re
import time

import alembic.command
import alembic.config
from sqlalchemy import MetaData, create_engine, text

import rg_app.db.models

_SCHEME = "postgresql+psycopg"


def generate_url(
    username: str, password: str, dbname: str = "postgres", host: str = "localhost", port: str = "5432"
) -> str:
    return f"{_SCHEME}://{username}:{password}@{host}:{port}/{dbname}"


def migrate(db_url: str):
    pkg_path = os.path.dirname(rg_app.db.__file__)

    if not re.match(r"^[a-z]+(\+[a-z]+)?://", db_url):
        db_url = f"{_SCHEME}://{db_url}"

    alembic_cfg = alembic.config.Config(os.path.join(pkg_path, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", os.path.join(pkg_path, "alembic"))
    engine = create_engine(db_url)
    success = False
    for _ in range(10):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                success = True
            break
        except Exception as e:
            print(e)
            time.sleep(5)
    if not success:
        raise Exception("Could not connect to the database")
    alembic.command.upgrade(alembic_cfg, "head")


def obtain_metadata() -> MetaData:
    from rg_app.db.models import Base

    # this import is necessary to register the models
    return Base.metadata
