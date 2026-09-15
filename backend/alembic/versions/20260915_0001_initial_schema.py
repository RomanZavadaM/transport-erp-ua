"""Initial TransportERP-UA physical schema.

Revision ID: 20260915_0001
Revises: None
Create Date: 2026-09-15
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260915_0001"
down_revision = None
branch_labels = None
depends_on = None

_SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
_UPGRADE_FILES = (
    "001_extensions.sql",
    "010_identity_foundation.sql",
    "020_fleet_drivers.sql",
    "030_routes_planning_trips.sql",
    "040_duties_release.sql",
    "050_documents_maintenance.sql",
    "060_system_constraints.sql",
    "070_rls_immutability.sql",
)


def _execute_sql_file(filename: str) -> None:
    sql = (_SQL_DIR / filename).read_text(encoding="utf-8")
    op.get_bind().exec_driver_sql(sql)


def upgrade() -> None:
    for filename in _UPGRADE_FILES:
        _execute_sql_file(filename)


def downgrade() -> None:
    _execute_sql_file("999_downgrade.sql")
