"""Identity and access bootstrap.

Revision ID: 20260915_0002
Revises: 20260915_0001
Create Date: 2026-09-15
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260915_0002"
down_revision = "20260915_0001"
branch_labels = None
depends_on = None

_SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def _execute_sql_file(filename: str) -> None:
    sql = (_SQL_DIR / filename).read_text(encoding="utf-8")
    op.get_bind().exec_driver_sql(sql)


def upgrade() -> None:
    _execute_sql_file("080_identity_access.sql")


def downgrade() -> None:
    _execute_sql_file("081_identity_access_downgrade.sql")
