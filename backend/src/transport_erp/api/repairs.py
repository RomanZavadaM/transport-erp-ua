from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Repairs"])

Severity = Literal["MINOR", "MAJOR", "CRITICAL"]
DefectStatus = Literal["OPEN", "IN_REPAIR", "RESOLVED", "CLOSED"]
RepairStatus = Literal["OPEN", "IN_PROGRESS", "COMPLETED", "CLOSED", "CANCELLED"]
ItemType = Literal["WORK", "PART", "MATERIAL"]


class DefectInput(BaseModel):
    description: str = Field(min_length=1, max_length=1500)
    severity: Severity = "MINOR"
    blocks_release: bool = False
    source: str = Field(default="TECHNICAL", min_length=1, max_length=80)
    reported_by: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=1000)


class DefectResponse(BaseModel):
    id: str
    vehicle_id: str
    reported_at: datetime
    reported_by: str | None
    source: str
    severity: Severity
    description: str
    blocks_release: bool
    status: DefectStatus
    note: str | None
    resolved_at: datetime | None


class RepairOrderInput(BaseModel):
    number: str = Field(min_length=1, max_length=80)
    defect_id: str | None = None
    description: str = Field(min_length=1, max_length=1500)
    provider: str | None = Field(default=None, max_length=240)
    blocks_operation: bool = True
    odometer_km: int | None = Field(default=None, ge=0)


class RepairItemInput(BaseModel):
    item_type: ItemType
    description: str = Field(min_length=1, max_length=1000)
    part_number: str | None = Field(default=None, max_length=120)
    quantity: float = Field(default=1, gt=0)
    unit: str = Field(default="шт", min_length=1, max_length=30)
    unit_price: float | None = Field(default=None, ge=0)


class RepairItemResponse(RepairItemInput):
    id: str
    amount: float | None


class RepairCloseInput(BaseModel):
    closed_by: str = Field(min_length=1, max_length=160)
    verification_comment: str = Field(min_length=1, max_length=1500)


class RepairOrderResponse(BaseModel):
    id: str
    vehicle_id: str
    defect_id: str | None
    number: str
    status: RepairStatus
    blocks_operation: bool
    opened_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    closed_at: datetime | None
    closed_by: str | None
    provider: str | None
    odometer_km: int | None
    description: str
    verification_comment: str | None
    total_cost: float
    items: list[RepairItemResponse]


class RepairSummary(BaseModel):
    vehicle_id: str
    defects: list[DefectResponse]
    repair_orders: list[RepairOrderResponse]


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local repair API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    _ensure_storage(connection)
    if write:
        connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
        if write:
            connection.commit()
    except Exception:
        if write:
            connection.rollback()
        raise
    finally:
        connection.close()


def _ensure_storage(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS defects (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
            reported_at TEXT NOT NULL,
            reported_by TEXT,
            source TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('MINOR','MAJOR','CRITICAL')),
            description TEXT NOT NULL,
            blocks_release INTEGER NOT NULL DEFAULT 0 CHECK (blocks_release IN (0,1)),
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN','IN_REPAIR','RESOLVED','CLOSED')),
            note TEXT,
            resolved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS repair_orders (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
            defect_id TEXT REFERENCES defects(id) ON DELETE SET NULL,
            number TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN','IN_PROGRESS','COMPLETED','CLOSED','CANCELLED')),
            blocks_operation INTEGER NOT NULL DEFAULT 1 CHECK (blocks_operation IN (0,1)),
            opened_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            closed_at TEXT,
            closed_by TEXT,
            provider TEXT,
            odometer_km INTEGER CHECK (odometer_km IS NULL OR odometer_km >= 0),
            description TEXT NOT NULL,
            verification_comment TEXT
        );

        CREATE TABLE IF NOT EXISTS repair_order_items (
            id TEXT PRIMARY KEY,
            repair_order_id TEXT NOT NULL REFERENCES repair_orders(id) ON DELETE CASCADE,
            item_type TEXT NOT NULL CHECK (item_type IN ('WORK','PART','MATERIAL')),
            description TEXT NOT NULL,
            part_number TEXT,
            quantity REAL NOT NULL CHECK (quantity > 0),
            unit TEXT NOT NULL,
            unit_price REAL CHECK (unit_price IS NULL OR unit_price >= 0),
            amount REAL CHECK (amount IS NULL OR amount >= 0)
        );

        CREATE INDEX IF NOT EXISTS idx_defects_vehicle_status
            ON defects(vehicle_id, status, blocks_release);
        CREATE INDEX IF NOT EXISTS idx_repair_orders_vehicle_status
            ON repair_orders(vehicle_id, status, blocks_operation);
        CREATE INDEX IF NOT EXISTS idx_repair_items_order
            ON repair_order_items(repair_order_id);
        """
    )


def _company_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = 'company_id'").fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Підприємство не ініціалізоване.")
    return str(row["value"])


def _require_vehicle(connection: sqlite3.Connection, vehicle_id: str) -> None:
    row = connection.execute(
        "SELECT id FROM vehicles WHERE id = ? AND company_id = ?",
        (vehicle_id, _company_id(connection)),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Автобус не знайдено.")


def _defect_from_row(row: sqlite3.Row) -> DefectResponse:
    return DefectResponse(
        id=str(row["id"]),
        vehicle_id=str(row["vehicle_id"]),
        reported_at=datetime.fromisoformat(str(row["reported_at"])),
        reported_by=str(row["reported_by"]) if row["reported_by"] is not None else None,
        source=str(row["source"]),
        severity=cast(Severity, str(row["severity"])),
        description=str(row["description"]),
        blocks_release=bool(row["blocks_release"]),
        status=cast(DefectStatus, str(row["status"])),
        note=str(row["note"]) if row["note"] is not None else None,
        resolved_at=(datetime.fromisoformat(str(row["resolved_at"])) if row["resolved_at"] else None),
    )


def _items(connection: sqlite3.Connection, order_id: str) -> list[RepairItemResponse]:
    rows = connection.execute(
        "SELECT * FROM repair_order_items WHERE repair_order_id = ? ORDER BY rowid",
        (order_id,),
    ).fetchall()
    return [
        RepairItemResponse(
            id=str(row["id"]),
            item_type=cast(ItemType, str(row["item_type"])),
            description=str(row["description"]),
            part_number=str(row["part_number"]) if row["part_number"] is not None else None,
            quantity=float(row["quantity"]),
            unit=str(row["unit"]),
            unit_price=float(row["unit_price"]) if row["unit_price"] is not None else None,
            amount=float(row["amount"]) if row["amount"] is not None else None,
        )
        for row in rows
    ]


def _order_from_row(connection: sqlite3.Connection, row: sqlite3.Row) -> RepairOrderResponse:
    items = _items(connection, str(row["id"]))
    return RepairOrderResponse(
        id=str(row["id"]),
        vehicle_id=str(row["vehicle_id"]),
        defect_id=str(row["defect_id"]) if row["defect_id"] is not None else None,
        number=str(row["number"]),
        status=cast(RepairStatus, str(row["status"])),
        blocks_operation=bool(row["blocks_operation"]),
        opened_at=datetime.fromisoformat(str(row["opened_at"])),
        started_at=datetime.fromisoformat(str(row["started_at"])) if row["started_at"] else None,
        completed_at=(datetime.fromisoformat(str(row["completed_at"])) if row["completed_at"] else None),
        closed_at=datetime.fromisoformat(str(row["closed_at"])) if row["closed_at"] else None,
        closed_by=str(row["closed_by"]) if row["closed_by"] is not None else None,
        provider=str(row["provider"]) if row["provider"] is not None else None,
        odometer_km=int(row["odometer_km"]) if row["odometer_km"] is not None else None,
        description=str(row["description"]),
        verification_comment=(
            str(row["verification_comment"]) if row["verification_comment"] is not None else None
        ),
        total_cost=round(sum(item.amount or 0 for item in items), 2),
        items=items,
    )


def _summary(connection: sqlite3.Connection, vehicle_id: str) -> RepairSummary:
    defects = connection.execute(
        "SELECT * FROM defects WHERE vehicle_id = ? ORDER BY reported_at DESC",
        (vehicle_id,),
    ).fetchall()
    orders = connection.execute(
        "SELECT * FROM repair_orders WHERE vehicle_id = ? ORDER BY opened_at DESC",
        (vehicle_id,),
    ).fetchall()
    return RepairSummary(
        vehicle_id=vehicle_id,
        defects=[_defect_from_row(row) for row in defects],
        repair_orders=[_order_from_row(connection, row) for row in orders],
    )


def _require_order(connection: sqlite3.Connection, order_id: str) -> sqlite3.Row:
    row = connection.execute("SELECT * FROM repair_orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Ремонтний наряд не знайдено.")
    return cast(sqlite3.Row, row)


def _refresh_vehicle_status(connection: sqlite3.Connection, vehicle_id: str) -> None:
    blocker = connection.execute(
        """
        SELECT 1
        FROM defects
        WHERE vehicle_id = ? AND blocks_release = 1 AND status IN ('OPEN','IN_REPAIR')
        UNION ALL
        SELECT 1
        FROM repair_orders
        WHERE vehicle_id = ? AND blocks_operation = 1 AND status NOT IN ('CLOSED','CANCELLED')
        LIMIT 1
        """,
        (vehicle_id, vehicle_id),
    ).fetchone()
    if blocker is None:
        connection.execute(
            "UPDATE vehicles SET lifecycle_status = 'ACTIVE', updated_at = ? WHERE id = ? AND lifecycle_status = 'REPAIR'",
            (datetime.now(UTC).isoformat(), vehicle_id),
        )
    else:
        connection.execute(
            "UPDATE vehicles SET lifecycle_status = 'REPAIR', updated_at = ? WHERE id = ?",
            (datetime.now(UTC).isoformat(), vehicle_id),
        )


@router.get("/vehicles/{vehicle_id}/repairs", response_model=RepairSummary)
def get_vehicle_repairs(vehicle_id: str) -> RepairSummary:
    with _connection() as connection:
        _require_vehicle(connection, vehicle_id)
        return _summary(connection, vehicle_id)


@router.post("/vehicles/{vehicle_id}/defects", response_model=DefectResponse, status_code=201)
def create_defect(vehicle_id: str, payload: DefectInput) -> DefectResponse:
    defect_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    with _connection(write=True) as connection:
        _require_vehicle(connection, vehicle_id)
        connection.execute(
            """
            INSERT INTO defects(
                id, vehicle_id, reported_at, reported_by, source, severity,
                description, blocks_release, status, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
            """,
            (
                defect_id,
                vehicle_id,
                now,
                payload.reported_by.strip() if payload.reported_by else None,
                payload.source.strip(),
                payload.severity,
                payload.description.strip(),
                int(payload.blocks_release),
                payload.note.strip() if payload.note else None,
            ),
        )
        _refresh_vehicle_status(connection, vehicle_id)
        row = connection.execute("SELECT * FROM defects WHERE id = ?", (defect_id,)).fetchone()
        assert row is not None
        return _defect_from_row(row)


@router.post("/vehicles/{vehicle_id}/repair-orders", response_model=RepairOrderResponse, status_code=201)
def create_repair_order(vehicle_id: str, payload: RepairOrderInput) -> RepairOrderResponse:
    order_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    try:
        with _connection(write=True) as connection:
            _require_vehicle(connection, vehicle_id)
            if payload.defect_id:
                defect = connection.execute(
                    "SELECT id FROM defects WHERE id = ? AND vehicle_id = ?",
                    (payload.defect_id, vehicle_id),
                ).fetchone()
                if defect is None:
                    raise HTTPException(status_code=404, detail="Дефект не знайдено для цього автобуса.")
            connection.execute(
                """
                INSERT INTO repair_orders(
                    id, vehicle_id, defect_id, number, status, blocks_operation,
                    opened_at, provider, odometer_km, description
                ) VALUES (?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    vehicle_id,
                    payload.defect_id,
                    payload.number.strip(),
                    int(payload.blocks_operation),
                    now,
                    payload.provider.strip() if payload.provider else None,
                    payload.odometer_km,
                    payload.description.strip(),
                ),
            )
            if payload.defect_id:
                connection.execute(
                    "UPDATE defects SET status = 'IN_REPAIR' WHERE id = ?",
                    (payload.defect_id,),
                )
            _refresh_vehicle_status(connection, vehicle_id)
            row = _require_order(connection, order_id)
            return _order_from_row(connection, row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Ремонтний наряд з таким номером уже існує.") from exc


@router.post("/repair-orders/{order_id}/items", response_model=RepairOrderResponse)
def add_repair_item(order_id: str, payload: RepairItemInput) -> RepairOrderResponse:
    with _connection(write=True) as connection:
        order = _require_order(connection, order_id)
        if str(order["status"]) in {"CLOSED", "CANCELLED"}:
            raise HTTPException(status_code=409, detail="Закритий ремонтний наряд не редагується.")
        amount = round(payload.quantity * payload.unit_price, 2) if payload.unit_price is not None else None
        connection.execute(
            """
            INSERT INTO repair_order_items(
                id, repair_order_id, item_type, description, part_number,
                quantity, unit, unit_price, amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                order_id,
                payload.item_type,
                payload.description.strip(),
                payload.part_number.strip() if payload.part_number else None,
                payload.quantity,
                payload.unit.strip(),
                payload.unit_price,
                amount,
            ),
        )
        row = _require_order(connection, order_id)
        return _order_from_row(connection, row)


@router.post("/repair-orders/{order_id}/start", response_model=RepairOrderResponse)
def start_repair(order_id: str) -> RepairOrderResponse:
    with _connection(write=True) as connection:
        order = _require_order(connection, order_id)
        if str(order["status"]) != "OPEN":
            raise HTTPException(status_code=409, detail="Розпочати можна тільки відкритий ремонтний наряд.")
        now = datetime.now(UTC).isoformat()
        connection.execute(
            "UPDATE repair_orders SET status = 'IN_PROGRESS', started_at = ? WHERE id = ?",
            (now, order_id),
        )
        row = _require_order(connection, order_id)
        return _order_from_row(connection, row)


@router.post("/repair-orders/{order_id}/complete", response_model=RepairOrderResponse)
def complete_repair(order_id: str) -> RepairOrderResponse:
    with _connection(write=True) as connection:
        order = _require_order(connection, order_id)
        if str(order["status"]) not in {"OPEN", "IN_PROGRESS"}:
            raise HTTPException(status_code=409, detail="Цей ремонтний наряд не можна завершити.")
        now = datetime.now(UTC).isoformat()
        connection.execute(
            "UPDATE repair_orders SET status = 'COMPLETED', completed_at = ? WHERE id = ?",
            (now, order_id),
        )
        row = _require_order(connection, order_id)
        return _order_from_row(connection, row)


@router.post("/repair-orders/{order_id}/close", response_model=RepairOrderResponse)
def close_repair(order_id: str, payload: RepairCloseInput) -> RepairOrderResponse:
    with _connection(write=True) as connection:
        order = _require_order(connection, order_id)
        if str(order["status"]) != "COMPLETED":
            raise HTTPException(
                status_code=409,
                detail="Перед закриттям ремонт має бути позначений як виконаний.",
            )
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            UPDATE repair_orders
            SET status = 'CLOSED', closed_at = ?, closed_by = ?, verification_comment = ?
            WHERE id = ?
            """,
            (now, payload.closed_by.strip(), payload.verification_comment.strip(), order_id),
        )
        defect_id = str(order["defect_id"]) if order["defect_id"] is not None else None
        if defect_id:
            connection.execute(
                "UPDATE defects SET status = 'RESOLVED', resolved_at = ? WHERE id = ?",
                (now, defect_id),
            )
        _refresh_vehicle_status(connection, str(order["vehicle_id"]))
        row = _require_order(connection, order_id)
        return _order_from_row(connection, row)
