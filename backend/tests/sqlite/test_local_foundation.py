from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from transport_erp.identity.application.service import IdentityService
from transport_erp.infrastructure.database import create_database_engine
from transport_erp.infrastructure.local_migrations import (
    downgrade_local_database,
    local_schema_tables,
    upgrade_local_database,
)
from transport_erp.local_node.bootstrap import initialize_local_node
from transport_erp.local_node.transfer import (
    RecordNotLocallyMutableError,
    TransferItemSpec,
    apply_central_ack,
    approve_transfer_batch,
    assert_local_mutable,
    cancel_transfer_batch,
    mark_transfer_attempt,
    prepare_transfer_batch,
    retry_failed_transfer,
)


@pytest.fixture
def local_database(tmp_path: Path) -> Iterator[tuple[str, Engine]]:
    database_path = tmp_path / "transporterp.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    upgrade_local_database(database_url)
    engine = create_database_engine(database_url)
    try:
        yield database_url, engine
    finally:
        engine.dispose()


def _bootstrap(engine: Engine) -> tuple[object, object, object]:
    with Session(engine, expire_on_commit=False) as session:
        result = initialize_local_node(
            session,
            company_name="АТП Тест",
            legal_name="ТОВ АТП Тест",
            edrpou="12345678",
            admin_username="admin",
            admin_password="Correct Horse Battery Staple",
            node_name="Головний ПК",
        )
    return result.company_id, result.admin_user_id, result.node_id


def test_local_migration_creates_foundation_and_pragmas(
    local_database: tuple[str, Engine],
) -> None:
    database_url, engine = local_database
    expected = {
        "companies",
        "users",
        "user_sessions",
        "roles",
        "permissions",
        "local_nodes",
        "transfer_requests",
        "transfer_batches",
        "transfer_items",
        "transfer_delivery_queue",
        "record_authority",
        "audit_log",
        "backup_runs",
        "system_integrity_alerts",
    }
    assert expected <= local_schema_tables(database_url)

    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        assert connection.execute(text("PRAGMA busy_timeout")).scalar_one() == 5000


def test_bootstrap_persists_node_and_identity_login(
    local_database: tuple[str, Engine],
) -> None:
    database_url, engine = local_database
    company_id, admin_user_id, node_id = _bootstrap(engine)

    with Session(engine, expire_on_commit=False) as session:
        issue = IdentityService(session_ttl_minutes=60).login(
            session,
            company_edrpou="12345678",
            username="admin",
            password="Correct Horse Battery Staple",
            ip_address="127.0.0.1",
            user_agent="sqlite-acceptance-test",
        )
        assert issue.principal.company_id == company_id
        assert issue.principal.user_id == admin_user_id
        assert "user.read" in issue.principal.permissions
        assert "settings.manage" in issue.principal.permissions
        assert "release.authorize" not in issue.principal.permissions

    engine.dispose()
    restarted_engine = create_database_engine(database_url)
    try:
        with restarted_engine.connect() as connection:
            persisted_node = connection.execute(
                text("SELECT id FROM local_nodes WHERE active = 1")
            ).scalar_one()
            assert persisted_node == str(node_id)
    finally:
        restarted_engine.dispose()


def test_transfer_requires_local_approval_and_ack_changes_authority(
    local_database: tuple[str, Engine],
) -> None:
    _database_url, engine = local_database
    _company_id, admin_user_id, node_id = _bootstrap(engine)
    entity_id = uuid4()

    with Session(engine, expire_on_commit=False) as session:
        batch_id = prepare_transfer_batch(
            session,
            node_id=node_id,
            prepared_reason="MANUAL",
            prepared_by=admin_user_id,
            items=[
                TransferItemSpec(
                    entity_type="test_record",
                    entity_id=entity_id,
                    entity_version=1,
                    payload_checksum="a" * 64,
                )
            ],
        )
        assert_local_mutable(session, entity_type="test_record", entity_id=entity_id)

        authority = session.execute(
            text(
                """
                SELECT authority, transfer_lock_batch_id
                FROM record_authority
                WHERE entity_type = 'test_record' AND entity_id = :entity_id
                """
            ),
            {"entity_id": str(entity_id)},
        ).mappings().one()
        assert authority["authority"] == "LOCAL"
        assert authority["transfer_lock_batch_id"] is None

        approve_transfer_batch(session, batch_id=batch_id, operator_id=admin_user_id)
        authority = session.execute(
            text(
                """
                SELECT authority, transfer_lock_batch_id
                FROM record_authority
                WHERE entity_type = 'test_record' AND entity_id = :entity_id
                """
            ),
            {"entity_id": str(entity_id)},
        ).mappings().one()
        assert authority["authority"] == "LOCAL"
        assert authority["transfer_lock_batch_id"] == str(batch_id)
        with pytest.raises(RecordNotLocallyMutableError, match="RECORD_LOCKED_FOR_TRANSFER"):
            assert_local_mutable(session, entity_type="test_record", entity_id=entity_id)

        mark_transfer_attempt(
            session,
            batch_id=batch_id,
            error_code="NETWORK_UNAVAILABLE",
            error_message="central is offline",
        )
        status = session.execute(
            text("SELECT status FROM transfer_batches WHERE id = :id"),
            {"id": str(batch_id)},
        ).scalar_one()
        assert status == "FAILED"
        authority = session.execute(
            text("SELECT authority FROM record_authority WHERE entity_id = :id"),
            {"id": str(entity_id)},
        ).scalar_one()
        assert authority == "LOCAL"

        retry_failed_transfer(session, batch_id=batch_id)
        apply_central_ack(
            session,
            batch_id=batch_id,
            central_ack_id="ack-test-0001",
            central_version=1,
        )
        authority = session.execute(
            text(
                """
                SELECT authority, transfer_lock_batch_id, central_ack_id
                FROM record_authority
                WHERE entity_type = 'test_record' AND entity_id = :entity_id
                """
            ),
            {"entity_id": str(entity_id)},
        ).mappings().one()
        assert authority["authority"] == "CENTRAL"
        assert authority["transfer_lock_batch_id"] is None
        assert authority["central_ack_id"] == "ack-test-0001"
        with pytest.raises(RecordNotLocallyMutableError, match="RECORD_MANAGED_CENTRALLY"):
            assert_local_mutable(session, entity_type="test_record", entity_id=entity_id)

        actions = session.execute(
            text("SELECT action FROM audit_log ORDER BY occurred_at, id")
        ).scalars().all()
        assert "TRANSFER_PREPARED" in actions
        assert "TRANSFER_APPROVED" in actions
        assert "TRANSFER_FAILED" in actions
        assert "TRANSFER_ACKNOWLEDGED" in actions


def test_failed_transfer_can_be_cancelled_and_unlocked(
    local_database: tuple[str, Engine],
) -> None:
    _database_url, engine = local_database
    _company_id, admin_user_id, node_id = _bootstrap(engine)
    entity_id = uuid4()

    with Session(engine, expire_on_commit=False) as session:
        batch_id = prepare_transfer_batch(
            session,
            node_id=node_id,
            prepared_reason="RULE",
            prepared_by=None,
            items=[
                TransferItemSpec(
                    entity_type="test_record",
                    entity_id=entity_id,
                    entity_version=1,
                    payload_checksum="b" * 64,
                )
            ],
        )
        approve_transfer_batch(session, batch_id=batch_id, operator_id=admin_user_id)
        mark_transfer_attempt(
            session,
            batch_id=batch_id,
            error_code="NETWORK_UNAVAILABLE",
        )
        cancel_transfer_batch(session, batch_id=batch_id, operator_id=admin_user_id)
        assert_local_mutable(session, entity_type="test_record", entity_id=entity_id)
        row = session.execute(
            text(
                """
                SELECT authority, transfer_lock_batch_id
                FROM record_authority
                WHERE entity_type = 'test_record' AND entity_id = :entity_id
                """
            ),
            {"entity_id": str(entity_id)},
        ).mappings().one()
        assert row["authority"] == "LOCAL"
        assert row["transfer_lock_batch_id"] is None


def test_database_rejects_transfer_without_operator_approval(
    local_database: tuple[str, Engine],
) -> None:
    _database_url, engine = local_database
    _company_id, _admin_user_id, node_id = _bootstrap(engine)

    with Session(engine) as session, pytest.raises(IntegrityError):
        with session.begin():
            session.execute(
                text(
                    """
                    INSERT INTO transfer_batches (
                        id, origin_node_id, status, prepared_reason
                    )
                    VALUES (:id, :node_id, 'TRANSFERRING', 'CENTRAL_REQUEST')
                    """
                ),
                {"id": str(uuid4()), "node_id": str(node_id)},
            )


def test_audit_log_is_append_only(local_database: tuple[str, Engine]) -> None:
    _database_url, engine = local_database
    _company_id, _admin_user_id, _node_id = _bootstrap(engine)

    with Session(engine) as session, pytest.raises(IntegrityError):
        with session.begin():
            session.execute(text("UPDATE audit_log SET action = 'TAMPERED'"))


def test_local_schema_can_downgrade_to_base(tmp_path: Path) -> None:
    database_path = tmp_path / "downgrade.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    upgrade_local_database(database_url)
    downgrade_local_database(database_url)
    assert local_schema_tables(database_url) == {"alembic_version"} or local_schema_tables(
        database_url
    ) == set()
