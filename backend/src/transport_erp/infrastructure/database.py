from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from transport_erp.config import get_settings


def _configure_sqlite_connection(dbapi_connection: Any, _: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=FULL")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    database_url = settings.resolved_database_url

    if database_url.startswith("sqlite"):
        settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        event.listen(engine, "connect", _configure_sqlite_connection)
        return engine

    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), class_=Session, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


def set_tenant_context(session: Session, company_id: UUID) -> None:
    if session.get_bind().dialect.name == "sqlite":
        return
    session.execute(
        text("SELECT set_config('app.company_id', :company_id, true)"),
        {"company_id": str(company_id)},
    )
