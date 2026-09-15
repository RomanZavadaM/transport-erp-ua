from __future__ import annotations

import os
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import Connection


def _database_url() -> str:
    url = os.getenv("TRANSPORT_ERP_TEST_DATABASE_URL") or os.getenv("TRANSPORT_ERP_DATABASE_URL")
    if not url:
        pytest.skip("PostgreSQL integration database is not configured")
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.fixture
def pg() -> Iterator[Connection[tuple[object, ...]]]:
    connection: Connection[tuple[object, ...]] = psycopg.connect(_database_url(), autocommit=True)
    try:
        yield connection
    finally:
        connection.close()
