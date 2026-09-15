from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.engine.reflection import Inspector

from alembic import command


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def local_alembic_config(database_url: str) -> Config:
    if make_url(database_url).get_backend_name() != "sqlite":
        raise ValueError("Local migrations require a SQLite database URL")
    root = _backend_root()
    config = Config(str(root / "alembic-local.ini"))
    config.set_main_option("script_location", str(root / "alembic_local"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade_local_database(database_url: str, revision: str = "head") -> None:
    command.upgrade(local_alembic_config(database_url), revision)


def downgrade_local_database(database_url: str, revision: str = "base") -> None:
    command.downgrade(local_alembic_config(database_url), revision)


def local_schema_tables(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        inspector: Inspector = inspect(engine)
        return set(inspector.get_table_names())
    finally:
        engine.dispose()
