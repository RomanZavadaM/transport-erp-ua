from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from transport_erp.config import get_settings


def _configure_sqlite_connection(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA busy_timeout = 5000")
    finally:
        cursor.close()


def _ensure_sqlite_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str) -> Engine:
    _ensure_sqlite_parent(database_url)
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    connect_args: dict[str, object] = {"check_same_thread": False} if is_sqlite else {}
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    if is_sqlite:
        event.listen(engine, "connect", _configure_sqlite_connection)
    return engine


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    database_url = settings.database_url
    assert database_url is not None
    return create_database_engine(database_url)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), class_=Session, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


def set_tenant_context(session: Session, company_id: UUID) -> None:
    bind = session.get_bind()
    if bind.dialect.name == "sqlite":
        return
    session.execute(
        text("SELECT set_config('app.company_id', :company_id, true)"),
        {"company_id": str(company_id)},
    )
