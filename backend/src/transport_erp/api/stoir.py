from __future__ import annotations

import calendar
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["STOIR"])

PlanKind = Literal["MAINTENANCE", "INSPECTION", "OTK", "CUSTOM"]
BasisSource = Literal["MANUFACTURER", "NORMATIVE", "ENTERPRISE", "CUSTOM"]
PlanState = Literal["NEEDS_BASELINE", "OK", "DUE_SOON", "OVERDUE"]
EventOutcome = Literal["COMPLETED", "PASSED", "FAILED"]


class StoirPlanInput(BaseModel):
    plan_kind: PlanKind
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    basis_source: BasisSource
    interval_km: int | None = Field(default=None, gt=0)
    interval_months: int | None = Field(default=None, gt=0, le=120)
    last_completed_date: date | None = None
    last_completed_odometer: int | None = Field(default=None, ge=0)
    warning_km: int = Field(default=500, ge=0)
    warning_days: int = Field(default=14, ge=0)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_interval(self) -> "StoirPlanInput":
        if self.interval_km is None and self.interval_months is None:
            raise ValueError("Потрібен інтервал хоча б у кілометрах або місяцях.")
        return self


class StoirPlanResponse(StoirPlanInput):
    id: str
    vehicle_id: str
    active: bool
    next_due_date: date | None
    next_due_odometer: int | None
    current_odometer: int | None
    remaining_km: int | None
    remaining_days: int | None
    state: PlanState
    created_at: datetime
    updated_at: datetime


class StoirCompletionInput(BaseModel):
    completed_date: date
    odometer_km: int | None = Field(default=None, ge=0)
    outcome: EventOutcome = "COMPLETED"
    performed_by: str | None = Field(default=None, max_length=160)
    provider: str | None = Field(default=None, max_length=240)
    document_number: str | None = Field(default=None, max_length=120)
    document_valid_until: date | None = None
    comment: str | None = Field(default=None, max_length=1500)


class StoirEventResponse(BaseModel):
    id: str
    vehicle_id: str
    plan_id: str | None
    plan_code: str | None
    plan_name: str | None
    plan_kind: str
    completed_date: date
    odometer_km: int | None
    outcome: EventOutcome
    performed_by: str | None
    provider: str | None
    document_number: str | None
    document_valid_until: date | None
    comment: str | None
    created_at: datetime


class StoirSummary(BaseModel):
    vehicle_id: str
    current_odometer: int | None
    plans: list[StoirPlanResponse]
    history: list[StoirEventResponse]


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local STOIR API is disabled")
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
        CREATE TABLE IF NOT EXISTS odometer_readings (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            reading_km INTEGER NOT NULL CHECK (reading_km >= 0),
            recorded_at TEXT NOT NULL,
            note TEXT
        );

        CREATE TABLE IF NOT EXISTS stoir_plans (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            plan_kind TEXT NOT NULL
                CHECK (plan_kind IN ('MAINTENANCE','INSPECTION','OTK','CUSTOM')),
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            basis_source TEXT NOT NULL
                CHECK (basis_source IN ('MANUFACTURER','NORMATIVE','ENTERPRISE','CUSTOM')),
            interval_km INTEGER CHECK (interval_km IS NULL OR interval_km > 0),
            interval_months INTEGER CHECK (interval_months IS NULL OR interval_months > 0),
            last_completed_date TEXT,
            last_completed_odometer INTEGER
                CHECK (last_completed_odometer IS NULL OR last_completed_odometer >= 0),
            next_due_date TEXT,
            next_due_odometer INTEGER
                CHECK (next_due_odometer IS NULL OR next_due_odometer >= 0),
            warning_km INTEGER NOT NULL DEFAULT 500 CHECK (warning_km >= 0),
            warning_days INTEGER NOT NULL DEFAULT 14 CHECK (warning_days >= 0),
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(vehicle_id, code),
            CHECK (interval_km IS NOT NULL OR interval_months IS NOT NULL)
        );

        CREATE TABLE IF NOT EXISTS stoir_events (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
            plan_id TEXT REFERENCES stoir_plans(id) ON DELETE SET NULL,
            plan_kind TEXT NOT NULL,
            completed_date TEXT NOT NULL,
            odometer_km INTEGER CHECK (odometer_km IS NULL OR odometer_km >= 0),
            outcome TEXT NOT NULL CHECK (outcome IN ('COMPLETED','PASSED','FAILED')),
            performed_by TEXT,
            provider TEXT,
            document_number TEXT,
            document_valid_until TEXT,
            comment TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_stoir_plans_vehicle_active
            ON stoir_plans(vehicle_id, active, code);
        CREATE INDEX IF NOT EXISTS idx_stoir_events_vehicle_date
            ON stoir_events(vehicle_id, completed_date DESC, created_at DESC);
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


def _current_odometer(connection: sqlite3.Connection, vehicle_id: str) -> int | None:
    row = connection.execute(
        """
        SELECT reading_km
        FROM odometer_readings
        WHERE vehicle_id = ?
        ORDER BY recorded_at DESC, rowid DESC
        LIMIT 1
        """,
        (vehicle_id,),
    ).fetchone()
    return int(row["reading_km"]) if row is not None else None


def _next_due_date(last_completed_date: date | None, interval_months: int | None) -> date | None:
    if last_completed_date is None or interval_months is None:
        return None
    return _add_months(last_completed_date, interval_months)


def _next_due_odometer(last_odometer: int | None, interval_km: int | None) -> int | None:
    if last_odometer is None or interval_km is None:
        return None
    return last_odometer + interval_km


def _plan_state(
    *,
    current_odometer: int | None,
    next_due_odometer: int | None,
    next_due_date: date | None,
    warning_km: int,
    warning_days: int,
) -> tuple[PlanState, int | None, int | None]:
    remaining_km = (
        next_due_odometer - current_odometer
        if next_due_odometer is not None and current_odometer is not None
        else None
    )
    remaining_days = (next_due_date - date.today()).days if next_due_date is not None else None

    if next_due_odometer is None and next_due_date is None:
        return "NEEDS_BASELINE", remaining_km, remaining_days
    if (remaining_km is not None and remaining_km < 0) or (
        remaining_days is not None and remaining_days < 0
    ):
        return "OVERDUE", remaining_km, remaining_days
    if (remaining_km is not None and remaining_km <= warning_km) or (
        remaining_days is not None and remaining_days <= warning_days
    ):
        return "DUE_SOON", remaining_km, remaining_days
    return "OK", remaining_km, remaining_days


def _plan_from_row(
    row: sqlite3.Row,
    current_odometer: int | None,
) -> StoirPlanResponse:
    last_date = date.fromisoformat(str(row["last_completed_date"])) if row["last_completed_date"] else None
    next_date = date.fromisoformat(str(row["next_due_date"])) if row["next_due_date"] else None
    next_odo = int(row["next_due_odometer"]) if row["next_due_odometer"] is not None else None
    warning_km = int(row["warning_km"])
    warning_days = int(row["warning_days"])
    state, remaining_km, remaining_days = _plan_state(
        current_odometer=current_odometer,
        next_due_odometer=next_odo,
        next_due_date=next_date,
        warning_km=warning_km,
        warning_days=warning_days,
    )
    return StoirPlanResponse(
        id=str(row["id"]),
        vehicle_id=str(row["vehicle_id"]),
        plan_kind=str(row["plan_kind"]),
        code=str(row["code"]),
        name=str(row["name"]),
        basis_source=str(row["basis_source"]),
        interval_km=int(row["interval_km"]) if row["interval_km"] is not None else None,
        interval_months=(
            int(row["interval_months"]) if row["interval_months"] is not None else None
        ),
        last_completed_date=last_date,
        last_completed_odometer=(
            int(row["last_completed_odometer"])
            if row["last_completed_odometer"] is not None
            else None
        ),
        warning_km=warning_km,
        warning_days=warning_days,
        note=str(row["note"]) if row["note"] is not None else None,
        active=bool(row["active"]),
        next_due_date=next_date,
        next_due_odometer=next_odo,
        current_odometer=current_odometer,
        remaining_km=remaining_km,
        remaining_days=remaining_days,
        state=state,
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
    )


def _history(connection: sqlite3.Connection, vehicle_id: str) -> list[StoirEventResponse]:
    rows = connection.execute(
        """
        SELECT e.*, p.code AS plan_code, p.name AS plan_name
        FROM stoir_events e
        LEFT JOIN stoir_plans p ON p.id = e.plan_id
        WHERE e.vehicle_id = ?
        ORDER BY e.completed_date DESC, e.created_at DESC
        """,
        (vehicle_id,),
    ).fetchall()
    return [
        StoirEventResponse(
            id=str(row["id"]),
            vehicle_id=str(row["vehicle_id"]),
            plan_id=str(row["plan_id"]) if row["plan_id"] is not None else None,
            plan_code=str(row["plan_code"]) if row["plan_code"] is not None else None,
            plan_name=str(row["plan_name"]) if row["plan_name"] is not None else None,
            plan_kind=str(row["plan_kind"]),
            completed_date=date.fromisoformat(str(row["completed_date"])),
            odometer_km=int(row["odometer_km"]) if row["odometer_km"] is not None else None,
            outcome=str(row["outcome"]),
            performed_by=str(row["performed_by"]) if row["performed_by"] is not None else None,
            provider=str(row["provider"]) if row["provider"] is not None else None,
            document_number=(
                str(row["document_number"]) if row["document_number"] is not None else None
            ),
            document_valid_until=(
                date.fromisoformat(str(row["document_valid_until"]))
                if row["document_valid_until"]
                else None
            ),
            comment=str(row["comment"]) if row["comment"] is not None else None,
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )
        for row in rows
    ]


@router.get("/vehicles/{vehicle_id}/stoir", response_model=StoirSummary)
def get_vehicle_stoir(vehicle_id: str) -> StoirSummary:
    with _connection() as connection:
        _require_vehicle(connection, vehicle_id)
        current = _current_odometer(connection, vehicle_id)
        rows = connection.execute(
            "SELECT * FROM stoir_plans WHERE vehicle_id = ? ORDER BY active DESC, code COLLATE NOCASE",
            (vehicle_id,),
        ).fetchall()
        return StoirSummary(
            vehicle_id=vehicle_id,
            current_odometer=current,
            plans=[_plan_from_row(row, current) for row in rows],
            history=_history(connection, vehicle_id),
        )


@router.post(
    "/vehicles/{vehicle_id}/stoir/plans",
    response_model=StoirPlanResponse,
    status_code=201,
)
def create_stoir_plan(vehicle_id: str, payload: StoirPlanInput) -> StoirPlanResponse:
    plan_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    next_date = _next_due_date(payload.last_completed_date, payload.interval_months)
    next_odo = _next_due_odometer(payload.last_completed_odometer, payload.interval_km)
    try:
        with _connection(write=True) as connection:
            _require_vehicle(connection, vehicle_id)
            connection.execute(
                """
                INSERT INTO stoir_plans(
                    id, vehicle_id, plan_kind, code, name, basis_source,
                    interval_km, interval_months,
                    last_completed_date, last_completed_odometer,
                    next_due_date, next_due_odometer,
                    warning_km, warning_days, active, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    plan_id,
                    vehicle_id,
                    payload.plan_kind,
                    payload.code.strip().upper(),
                    payload.name.strip(),
                    payload.basis_source,
                    payload.interval_km,
                    payload.interval_months,
                    payload.last_completed_date.isoformat() if payload.last_completed_date else None,
                    payload.last_completed_odometer,
                    next_date.isoformat() if next_date else None,
                    next_odo,
                    payload.warning_km,
                    payload.warning_days,
                    payload.note.strip() if payload.note else None,
                    now,
                    now,
                ),
            )
            row = connection.execute("SELECT * FROM stoir_plans WHERE id = ?", (plan_id,)).fetchone()
            assert row is not None
            return _plan_from_row(row, _current_odometer(connection, vehicle_id))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Для цього автобуса план з таким кодом уже існує.",
        ) from exc


@router.post("/stoir/plans/{plan_id}/complete", response_model=StoirSummary)
def complete_stoir_plan(plan_id: str, payload: StoirCompletionInput) -> StoirSummary:
    with _connection(write=True) as connection:
        plan = connection.execute("SELECT * FROM stoir_plans WHERE id = ?", (plan_id,)).fetchone()
        if plan is None:
            raise HTTPException(status_code=404, detail="План СТОІР не знайдено.")
        vehicle_id = str(plan["vehicle_id"])
        _require_vehicle(connection, vehicle_id)
        current = _current_odometer(connection, vehicle_id)
        odometer = payload.odometer_km if payload.odometer_km is not None else current
        if current is not None and odometer is not None and odometer < current:
            raise HTTPException(
                status_code=409,
                detail=f"Пробіг виконання не може бути меншим за поточний одометр ({current} км).",
            )

        event_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            INSERT INTO stoir_events(
                id, vehicle_id, plan_id, plan_kind, completed_date, odometer_km,
                outcome, performed_by, provider, document_number,
                document_valid_until, comment, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                vehicle_id,
                plan_id,
                str(plan["plan_kind"]),
                payload.completed_date.isoformat(),
                odometer,
                payload.outcome,
                payload.performed_by.strip() if payload.performed_by else None,
                payload.provider.strip() if payload.provider else None,
                payload.document_number.strip() if payload.document_number else None,
                payload.document_valid_until.isoformat() if payload.document_valid_until else None,
                payload.comment.strip() if payload.comment else None,
                now,
            ),
        )

        if payload.outcome in {"COMPLETED", "PASSED"}:
            interval_km = int(plan["interval_km"]) if plan["interval_km"] is not None else None
            interval_months = (
                int(plan["interval_months"]) if plan["interval_months"] is not None else None
            )
            next_date = _next_due_date(payload.completed_date, interval_months)
            next_odo = _next_due_odometer(odometer, interval_km)
            if str(plan["plan_kind"]) == "OTK" and payload.document_valid_until is not None:
                next_date = payload.document_valid_until
            connection.execute(
                """
                UPDATE stoir_plans
                SET last_completed_date = ?, last_completed_odometer = ?,
                    next_due_date = ?, next_due_odometer = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload.completed_date.isoformat(),
                    odometer,
                    next_date.isoformat() if next_date else None,
                    next_odo,
                    now,
                    plan_id,
                ),
            )

        rows = connection.execute(
            "SELECT * FROM stoir_plans WHERE vehicle_id = ? ORDER BY active DESC, code COLLATE NOCASE",
            (vehicle_id,),
        ).fetchall()
        current_after = _current_odometer(connection, vehicle_id)
        return StoirSummary(
            vehicle_id=vehicle_id,
            current_odometer=current_after,
            plans=[_plan_from_row(row, current_after) for row in rows],
            history=_history(connection, vehicle_id),
        )
