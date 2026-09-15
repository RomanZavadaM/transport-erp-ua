from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class TransferStateError(RuntimeError):
    pass


class RecordNotLocallyMutableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TransferItemSpec:
    entity_type: str
    entity_id: UUID
    entity_version: int
    payload_checksum: str
    transfer_order: int = 0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _batch_checksum(items: list[TransferItemSpec]) -> str:
    canonical = "\n".join(
        f"{item.transfer_order}|{item.entity_type}|{item.entity_id}|"
        f"{item.entity_version}|{item.payload_checksum}"
        for item in sorted(
            items,
            key=lambda value: (
                value.transfer_order,
                value.entity_type,
                str(value.entity_id),
            ),
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sqlite(session: Session) -> None:
    if session.get_bind().dialect.name != "sqlite":
        raise ValueError("Local transfer workflow requires SQLite")


def register_local_record(session: Session, *, entity_type: str, entity_id: UUID) -> None:
    _require_sqlite(session)
    session.execute(
        text(
            """
            INSERT INTO record_authority (entity_type, entity_id, authority)
            VALUES (:entity_type, :entity_id, 'LOCAL')
            ON CONFLICT(entity_type, entity_id) DO NOTHING
            """
        ),
        {"entity_type": entity_type, "entity_id": str(entity_id)},
    )


def assert_local_mutable(session: Session, *, entity_type: str, entity_id: UUID) -> None:
    _require_sqlite(session)
    row = session.execute(
        text(
            """
            SELECT authority, transfer_lock_batch_id
            FROM record_authority
            WHERE entity_type = :entity_type AND entity_id = :entity_id
            """
        ),
        {"entity_type": entity_type, "entity_id": str(entity_id)},
    ).mappings().one_or_none()
    if row is None:
        return
    if row["authority"] != "LOCAL":
        raise RecordNotLocallyMutableError("RECORD_MANAGED_CENTRALLY")
    if row["transfer_lock_batch_id"] is not None:
        raise RecordNotLocallyMutableError("RECORD_LOCKED_FOR_TRANSFER")


def prepare_transfer_batch(
    session: Session,
    *,
    node_id: UUID,
    prepared_reason: str,
    items: list[TransferItemSpec],
    prepared_by: UUID | None,
    request_id: UUID | None = None,
) -> UUID:
    _require_sqlite(session)
    if prepared_reason not in {"MANUAL", "CENTRAL_REQUEST", "RULE"}:
        raise ValueError("Unsupported transfer preparation reason")
    if not items:
        raise ValueError("Transfer batch must contain at least one item")
    if any(item.entity_version < 1 for item in items):
        raise ValueError("Transfer item version must be >= 1")

    batch_id = uuid4()
    checksum = _batch_checksum(items)
    with session.begin():
        active_node = session.execute(
            text("SELECT 1 FROM local_nodes WHERE id = :id AND active = 1"),
            {"id": str(node_id)},
        ).scalar_one_or_none()
        if active_node is None:
            raise TransferStateError("LOCAL_NODE_NOT_ACTIVE")

        for item in items:
            register_local_record(
                session,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
            )
            assert_local_mutable(
                session,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
            )

        session.execute(
            text(
                """
                INSERT INTO transfer_batches (
                    id, origin_node_id, request_id, status, prepared_reason,
                    prepared_by, payload_checksum
                )
                VALUES (
                    :id, :origin_node_id, :request_id, 'PENDING_APPROVAL',
                    :prepared_reason, :prepared_by, :payload_checksum
                )
                """
            ),
            {
                "id": str(batch_id),
                "origin_node_id": str(node_id),
                "request_id": str(request_id) if request_id else None,
                "prepared_reason": prepared_reason,
                "prepared_by": str(prepared_by) if prepared_by else None,
                "payload_checksum": checksum,
            },
        )
        for item in items:
            session.execute(
                text(
                    """
                    INSERT INTO transfer_items (
                        transfer_batch_id, entity_type, entity_id, entity_version,
                        payload_checksum, transfer_order
                    )
                    VALUES (
                        :batch_id, :entity_type, :entity_id, :entity_version,
                        :payload_checksum, :transfer_order
                    )
                    """
                ),
                {
                    "batch_id": str(batch_id),
                    "entity_type": item.entity_type,
                    "entity_id": str(item.entity_id),
                    "entity_version": item.entity_version,
                    "payload_checksum": item.payload_checksum,
                    "transfer_order": item.transfer_order,
                },
            )
        _audit(
            session,
            node_id=node_id,
            actor_user_id=prepared_by,
            action="TRANSFER_PREPARED",
            entity_type="transfer_batch",
            entity_id=batch_id,
        )
    return batch_id


def approve_transfer_batch(
    session: Session,
    *,
    batch_id: UUID,
    operator_id: UUID,
) -> UUID:
    _require_sqlite(session)
    queue_id = uuid4()
    now = _utc_now()
    with session.begin():
        batch = session.execute(
            text(
                """
                SELECT origin_node_id, status, payload_checksum
                FROM transfer_batches
                WHERE id = :id
                """
            ),
            {"id": str(batch_id)},
        ).mappings().one_or_none()
        if batch is None:
            raise TransferStateError("TRANSFER_BATCH_NOT_FOUND")
        if batch["status"] != "PENDING_APPROVAL":
            raise TransferStateError("TRANSFER_BATCH_NOT_PENDING_APPROVAL")

        items = session.execute(
            text(
                """
                SELECT entity_type, entity_id
                FROM transfer_items
                WHERE transfer_batch_id = :batch_id
                ORDER BY transfer_order, entity_type, entity_id
                """
            ),
            {"batch_id": str(batch_id)},
        ).mappings().all()
        if not items:
            raise TransferStateError("TRANSFER_BATCH_EMPTY")

        for item in items:
            entity_id = UUID(str(item["entity_id"]))
            assert_local_mutable(
                session,
                entity_type=str(item["entity_type"]),
                entity_id=entity_id,
            )

        session.execute(
            text(
                """
                UPDATE transfer_batches
                SET status = 'TRANSFERRING', approved_at = :now,
                    approved_by = :operator_id, started_at = :now,
                    row_version = row_version + 1
                WHERE id = :batch_id
                """
            ),
            {
                "now": now,
                "operator_id": str(operator_id),
                "batch_id": str(batch_id),
            },
        )
        for item in items:
            session.execute(
                text(
                    """
                    UPDATE record_authority
                    SET transfer_lock_batch_id = :batch_id
                    WHERE entity_type = :entity_type AND entity_id = :entity_id
                      AND authority = 'LOCAL' AND transfer_lock_batch_id IS NULL
                    """
                ),
                {
                    "batch_id": str(batch_id),
                    "entity_type": str(item["entity_type"]),
                    "entity_id": str(item["entity_id"]),
                },
            )

        session.execute(
            text(
                """
                INSERT INTO transfer_delivery_queue (
                    id, transfer_batch_id, available_at
                )
                VALUES (:id, :batch_id, :available_at)
                """
            ),
            {
                "id": str(queue_id),
                "batch_id": str(batch_id),
                "available_at": now,
            },
        )
        _audit(
            session,
            node_id=UUID(str(batch["origin_node_id"])),
            actor_user_id=operator_id,
            action="TRANSFER_APPROVED",
            entity_type="transfer_batch",
            entity_id=batch_id,
        )
    return queue_id


def mark_transfer_attempt(
    session: Session,
    *,
    batch_id: UUID,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    _require_sqlite(session)
    now = _utc_now()
    with session.begin():
        batch = session.execute(
            text("SELECT origin_node_id, status FROM transfer_batches WHERE id = :id"),
            {"id": str(batch_id)},
        ).mappings().one_or_none()
        if batch is None:
            raise TransferStateError("TRANSFER_BATCH_NOT_FOUND")
        if batch["status"] not in {"TRANSFERRING", "FAILED"}:
            raise TransferStateError("TRANSFER_BATCH_NOT_DELIVERABLE")

        next_status = "FAILED" if error_code else "TRANSFERRING"
        session.execute(
            text(
                """
                UPDATE transfer_batches
                SET status = :status,
                    last_attempt_at = :now,
                    attempt_count = attempt_count + 1,
                    last_error_code = :error_code,
                    last_error_message = :error_message,
                    row_version = row_version + 1
                WHERE id = :batch_id
                """
            ),
            {
                "status": next_status,
                "now": now,
                "error_code": error_code,
                "error_message": error_message,
                "batch_id": str(batch_id),
            },
        )
        session.execute(
            text(
                """
                UPDATE transfer_delivery_queue
                SET last_attempt_at = :now,
                    attempt_count = attempt_count + 1,
                    last_error_code = :error_code,
                    last_error_message = :error_message
                WHERE transfer_batch_id = :batch_id
                """
            ),
            {
                "now": now,
                "error_code": error_code,
                "error_message": error_message,
                "batch_id": str(batch_id),
            },
        )
        _audit(
            session,
            node_id=UUID(str(batch["origin_node_id"])),
            actor_user_id=None,
            action="TRANSFER_FAILED" if error_code else "TRANSFER_ATTEMPTED",
            entity_type="transfer_batch",
            entity_id=batch_id,
            metadata_json=(
                f'{{"error_code":"{error_code}"}}' if error_code is not None else "{}"
            ),
        )


def retry_failed_transfer(session: Session, *, batch_id: UUID) -> None:
    _require_sqlite(session)
    with session.begin():
        result = session.execute(
            text(
                """
                UPDATE transfer_batches
                SET status = 'TRANSFERRING', row_version = row_version + 1
                WHERE id = :batch_id AND status = 'FAILED'
                """
            ),
            {"batch_id": str(batch_id)},
        )
        if result.rowcount != 1:
            raise TransferStateError("TRANSFER_BATCH_NOT_FAILED")
        session.execute(
            text(
                """
                UPDATE transfer_delivery_queue
                SET available_at = :available_at
                WHERE transfer_batch_id = :batch_id AND completed_at IS NULL
                """
            ),
            {"available_at": _utc_now(), "batch_id": str(batch_id)},
        )


def cancel_transfer_batch(
    session: Session,
    *,
    batch_id: UUID,
    operator_id: UUID,
) -> None:
    _require_sqlite(session)
    now = _utc_now()
    with session.begin():
        batch = session.execute(
            text("SELECT origin_node_id, status FROM transfer_batches WHERE id = :id"),
            {"id": str(batch_id)},
        ).mappings().one_or_none()
        if batch is None:
            raise TransferStateError("TRANSFER_BATCH_NOT_FOUND")
        if batch["status"] not in {"PENDING_APPROVAL", "FAILED"}:
            raise TransferStateError("TRANSFER_BATCH_CANNOT_BE_CANCELLED")

        session.execute(
            text(
                """
                UPDATE record_authority
                SET transfer_lock_batch_id = NULL
                WHERE transfer_lock_batch_id = :batch_id AND authority = 'LOCAL'
                """
            ),
            {"batch_id": str(batch_id)},
        )
        session.execute(
            text(
                """
                UPDATE transfer_batches
                SET status = 'CANCELLED', cancelled_at = :now,
                    cancelled_by = :operator_id, row_version = row_version + 1
                WHERE id = :batch_id
                """
            ),
            {
                "now": now,
                "operator_id": str(operator_id),
                "batch_id": str(batch_id),
            },
        )
        session.execute(
            text(
                """
                UPDATE transfer_delivery_queue
                SET completed_at = :now
                WHERE transfer_batch_id = :batch_id AND completed_at IS NULL
                """
            ),
            {"now": now, "batch_id": str(batch_id)},
        )
        _audit(
            session,
            node_id=UUID(str(batch["origin_node_id"])),
            actor_user_id=operator_id,
            action="TRANSFER_CANCELLED",
            entity_type="transfer_batch",
            entity_id=batch_id,
        )


def apply_central_ack(
    session: Session,
    *,
    batch_id: UUID,
    central_ack_id: str,
    central_version: int | None = None,
) -> None:
    _require_sqlite(session)
    if not central_ack_id.strip():
        raise ValueError("central_ack_id is required")
    now = _utc_now()

    with session.begin():
        batch = session.execute(
            text(
                """
                SELECT origin_node_id, status, approved_at, approved_by
                FROM transfer_batches
                WHERE id = :id
                """
            ),
            {"id": str(batch_id)},
        ).mappings().one_or_none()
        if batch is None:
            raise TransferStateError("TRANSFER_BATCH_NOT_FOUND")
        if batch["status"] not in {"TRANSFERRING", "FAILED"}:
            raise TransferStateError("TRANSFER_BATCH_NOT_AWAITING_ACK")
        if batch["approved_at"] is None or batch["approved_by"] is None:
            raise TransferStateError("TRANSFER_BATCH_NOT_APPROVED")

        session.execute(
            text(
                """
                UPDATE transfer_batches
                SET status = 'ACKNOWLEDGED', acknowledged_at = :now,
                    central_ack_id = :central_ack_id,
                    last_error_code = NULL, last_error_message = NULL,
                    row_version = row_version + 1
                WHERE id = :batch_id
                """
            ),
            {
                "now": now,
                "central_ack_id": central_ack_id,
                "batch_id": str(batch_id),
            },
        )
        session.execute(
            text(
                """
                UPDATE record_authority
                SET authority = 'CENTRAL', transfer_lock_batch_id = NULL,
                    central_version = :central_version,
                    central_ack_id = :central_ack_id,
                    central_synced_at = :now
                WHERE transfer_lock_batch_id = :batch_id AND authority = 'LOCAL'
                """
            ),
            {
                "central_version": central_version,
                "central_ack_id": central_ack_id,
                "now": now,
                "batch_id": str(batch_id),
            },
        )
        session.execute(
            text(
                """
                UPDATE transfer_delivery_queue
                SET completed_at = :now, last_error_code = NULL, last_error_message = NULL
                WHERE transfer_batch_id = :batch_id
                """
            ),
            {"now": now, "batch_id": str(batch_id)},
        )
        _audit(
            session,
            node_id=UUID(str(batch["origin_node_id"])),
            actor_user_id=None,
            action="TRANSFER_ACKNOWLEDGED",
            entity_type="transfer_batch",
            entity_id=batch_id,
            metadata_json=f'{{"central_ack_id":"{central_ack_id}"}}',
        )


def _audit(
    session: Session,
    *,
    node_id: UUID,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    metadata_json: str = "{}",
) -> None:
    session.execute(
        text(
            """
            INSERT INTO audit_log (
                id, actor_user_id, node_id, action, entity_type, entity_id,
                source, metadata_json
            )
            VALUES (
                :id, :actor_user_id, :node_id, :action, :entity_type, :entity_id,
                'LOCAL_APP', :metadata_json
            )
            """
        ),
        {
            "id": str(uuid4()),
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "node_id": str(node_id),
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "metadata_json": metadata_json,
        },
    )
