from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Release"])

CheckResult = Literal["PASSED", "FAILED"]
DispatcherResult = Literal["APPROVED", "REJECTED"]


class CheckInput(BaseModel):
    result: CheckResult
    checked_by: str = Field(min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=500)


class DispatcherInput(BaseModel):
    result: DispatcherResult
    checked_by: str = Field(min_length=1, max_length=120)
    note: str | None = Field(default=None, max_length=500)


class ReleaseResponse(BaseModel):
    duty_id: str
    service_date: str
    duty_number: str
    vehicle_label: str
    driver_label: str
    trip_count: int
    planned_departure: str
    planned_arrival: str
    medical_result: str
    medical_checked_by: str | None
    medical_checked_at: str | None
    medical_note: str | None
    technical_result: str
    technical_checked_by: str | None
    technical_checked_at: str | None
    technical_note: str | None
    dispatcher_result: str
    dispatcher_checked_by: str | None
    dispatcher_checked_at: str | None
    dispatcher_note: str | None
    released_at: str | None
    ready_to_release: bool


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local release API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS duty_release_controls (
            duty_id TEXT PRIMARY KEY REFERENCES duties(id) ON DELETE CASCADE,
            company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
            medical_result TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (medical_result IN ('PENDING','PASSED','FAILED')),
            medical_checked_by TEXT,
            medical_checked_at TEXT,
            medical_note TEXT,
            technical_result TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (technical_result IN ('PENDING','PASSED','FAILED')),
            technical_checked_by TEXT,
            technical_checked_at TEXT,
            technical_note TEXT,
            dispatcher_result TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (dispatcher_result IN ('PENDING','APPROVED','REJECTED')),
            dispatcher_checked_by TEXT,
            dispatcher_checked_at TEXT,
            dispatcher_note TEXT,
            released_at TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_release_controls_company ON duty_release_controls(company_id)"
    )
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


def _company_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = 'company_id'").fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Підприємство не ініціалізоване.")
    return str(row["value"])


def _ensure_control_row(
    connection: sqlite3.Connection, *, company_id: str, duty_id: str
) -> None:
    duty = connection.execute(
        "SELECT id FROM duties WHERE id = ? AND company_id = ?",
        (duty_id, company_id),
    ).fetchone()
    if duty is None:
        raise HTTPException(status_code=404, detail="Наряд не знайдено.")
    connection.execute(
        """
        INSERT OR IGNORE INTO duty_release_controls(duty_id, company_id, updated_at)
        VALUES (?, ?, ?)
        """,
        (duty_id, company_id, datetime.now(UTC).isoformat()),
    )


def _assert_editable(connection: sqlite3.Connection, duty_id: str) -> None:
    row = connection.execute(
        """
        SELECT d.status, c.released_at
        FROM duties d
        LEFT JOIN duty_release_controls c ON c.duty_id = d.id
        WHERE d.id = ?
        """,
        (duty_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Наряд не знайдено.")
    if str(row["status"]) in {"CANCELLED", "COMPLETED"}:
        raise HTTPException(status_code=409, detail="Цей наряд вже не можна змінювати.")
    if row["released_at"] is not None:
        raise HTTPException(status_code=409, detail="Наряд уже випущено на лінію.")


def _from_row(row: sqlite3.Row) -> ReleaseResponse:
    medical = str(row["medical_result"] or "PENDING")
    technical = str(row["technical_result"] or "PENDING")
    dispatcher = str(row["dispatcher_result"] or "PENDING")
    return ReleaseResponse(
        duty_id=str(row["duty_id"]),
        service_date=str(row["service_date"]),
        duty_number=str(row["duty_number"]),
        vehicle_label=f"{row['fleet_number']} — {row['registration_number']}",
        driver_label=" ".join(
            part for part in [row["last_name"], row["first_name"], row["middle_name"]] if part
        ),
        trip_count=int(row["trip_count"]),
        planned_departure=str(row["planned_departure"]),
        planned_arrival=str(row["planned_arrival"]),
        medical_result=medical,
        medical_checked_by=(
            str(row["medical_checked_by"]) if row["medical_checked_by"] is not None else None
        ),
        medical_checked_at=(
            str(row["medical_checked_at"]) if row["medical_checked_at"] is not None else None
        ),
        medical_note=str(row["medical_note"]) if row["medical_note"] is not None else None,
        technical_result=technical,
        technical_checked_by=(
            str(row["technical_checked_by"])
            if row["technical_checked_by"] is not None
            else None
        ),
        technical_checked_at=(
            str(row["technical_checked_at"])
            if row["technical_checked_at"] is not None
            else None
        ),
        technical_note=(
            str(row["technical_note"]) if row["technical_note"] is not None else None
        ),
        dispatcher_result=dispatcher,
        dispatcher_checked_by=(
            str(row["dispatcher_checked_by"])
            if row["dispatcher_checked_by"] is not None
            else None
        ),
        dispatcher_checked_at=(
            str(row["dispatcher_checked_at"])
            if row["dispatcher_checked_at"] is not None
            else None
        ),
        dispatcher_note=(
            str(row["dispatcher_note"]) if row["dispatcher_note"] is not None else None
        ),
        released_at=str(row["released_at"]) if row["released_at"] is not None else None,
        ready_to_release=(
            medical == "PASSED"
            and technical == "PASSED"
            and dispatcher == "APPROVED"
            and row["released_at"] is None
        ),
    )


def _load_controls(
    connection: sqlite3.Connection, company_id: str, service_date: str
) -> list[ReleaseResponse]:
    rows = connection.execute(
        """
        SELECT d.id AS duty_id, d.service_date, d.duty_number,
               v.fleet_number, v.registration_number,
               dr.last_name, dr.first_name, dr.middle_name,
               COUNT(dt.trip_id) AS trip_count,
               MIN(t.planned_departure) AS planned_departure,
               MAX(t.planned_arrival) AS planned_arrival,
               c.medical_result, c.medical_checked_by, c.medical_checked_at, c.medical_note,
               c.technical_result, c.technical_checked_by, c.technical_checked_at,
               c.technical_note, c.dispatcher_result, c.dispatcher_checked_by,
               c.dispatcher_checked_at, c.dispatcher_note, c.released_at
        FROM duties d
        JOIN vehicles v ON v.id = d.vehicle_id
        JOIN drivers dr ON dr.id = d.driver_id
        JOIN duty_trips dt ON dt.duty_id = d.id
        JOIN trips t ON t.id = dt.trip_id
        LEFT JOIN duty_release_controls c ON c.duty_id = d.id
        WHERE d.company_id = ? AND d.service_date = ? AND d.status <> 'CANCELLED'
        GROUP BY d.id
        ORDER BY planned_departure, d.duty_number COLLATE NOCASE
        """,
        (company_id, service_date),
    ).fetchall()
    return [_from_row(row) for row in rows]


@router.get("/release-controls", response_model=list[ReleaseResponse])
def list_release_controls(service_date: date = Query(...)) -> list[ReleaseResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        return _load_controls(connection, company_id, service_date.isoformat())


@router.post("/release-controls/{duty_id}/medical", response_model=ReleaseResponse)
def set_medical_check(duty_id: str, payload: CheckInput) -> ReleaseResponse:
    with _connection(write=True) as connection:
        company_id = _company_id(connection)
        _ensure_control_row(connection, company_id=company_id, duty_id=duty_id)
        _assert_editable(connection, duty_id)
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            UPDATE duty_release_controls
            SET medical_result = ?, medical_checked_by = ?, medical_checked_at = ?,
                medical_note = ?, updated_at = ?
            WHERE duty_id = ?
            """,
            (
                payload.result,
                payload.checked_by.strip(),
                now,
                payload.note.strip() if payload.note else None,
                now,
                duty_id,
            ),
        )
        return next(
            item
            for item in _load_controls(
                connection,
                company_id,
                str(
                    connection.execute(
                        "SELECT service_date FROM duties WHERE id = ?", (duty_id,)
                    ).fetchone()[0]
                ),
            )
            if item.duty_id == duty_id
        )


@router.post("/release-controls/{duty_id}/technical", response_model=ReleaseResponse)
def set_technical_check(duty_id: str, payload: CheckInput) -> ReleaseResponse:
    with _connection(write=True) as connection:
        company_id = _company_id(connection)
        _ensure_control_row(connection, company_id=company_id, duty_id=duty_id)
        _assert_editable(connection, duty_id)
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            UPDATE duty_release_controls
            SET technical_result = ?, technical_checked_by = ?, technical_checked_at = ?,
                technical_note = ?, updated_at = ?
            WHERE duty_id = ?
            """,
            (
                payload.result,
                payload.checked_by.strip(),
                now,
                payload.note.strip() if payload.note else None,
                now,
                duty_id,
            ),
        )
        service_date = str(
            connection.execute("SELECT service_date FROM duties WHERE id = ?", (duty_id,)).fetchone()[0]
        )
        return next(
            item
            for item in _load_controls(connection, company_id, service_date)
            if item.duty_id == duty_id
        )


@router.post("/release-controls/{duty_id}/dispatcher", response_model=ReleaseResponse)
def set_dispatcher_check(duty_id: str, payload: DispatcherInput) -> ReleaseResponse:
    with _connection(write=True) as connection:
        company_id = _company_id(connection)
        _ensure_control_row(connection, company_id=company_id, duty_id=duty_id)
        _assert_editable(connection, duty_id)
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            UPDATE duty_release_controls
            SET dispatcher_result = ?, dispatcher_checked_by = ?, dispatcher_checked_at = ?,
                dispatcher_note = ?, updated_at = ?
            WHERE duty_id = ?
            """,
            (
                payload.result,
                payload.checked_by.strip(),
                now,
                payload.note.strip() if payload.note else None,
                now,
                duty_id,
            ),
        )
        service_date = str(
            connection.execute("SELECT service_date FROM duties WHERE id = ?", (duty_id,)).fetchone()[0]
        )
        return next(
            item
            for item in _load_controls(connection, company_id, service_date)
            if item.duty_id == duty_id
        )


@router.post("/release-controls/{duty_id}/release", response_model=ReleaseResponse)
def release_duty(duty_id: str) -> ReleaseResponse:
    with _connection(write=True) as connection:
        company_id = _company_id(connection)
        _ensure_control_row(connection, company_id=company_id, duty_id=duty_id)
        _assert_editable(connection, duty_id)
        control = connection.execute(
            """
            SELECT medical_result, technical_result, dispatcher_result
            FROM duty_release_controls WHERE duty_id = ?
            """,
            (duty_id,),
        ).fetchone()
        if control is None:
            raise HTTPException(status_code=500, detail="Контроль випуску не ініціалізовано.")
        if str(control["medical_result"]) != "PASSED":
            raise HTTPException(status_code=409, detail="Немає позитивного медичного контролю.")
        if str(control["technical_result"]) != "PASSED":
            raise HTTPException(status_code=409, detail="Немає позитивного технічного контролю.")
        if str(control["dispatcher_result"]) != "APPROVED":
            raise HTTPException(status_code=409, detail="Немає дозволу диспетчера.")

        now = datetime.now(UTC).isoformat()
        connection.execute(
            "UPDATE duty_release_controls SET released_at = ?, updated_at = ? WHERE duty_id = ?",
            (now, now, duty_id),
        )
        connection.execute("UPDATE duties SET status = 'READY' WHERE id = ?", (duty_id,))
        service_date = str(
            connection.execute("SELECT service_date FROM duties WHERE id = ?", (duty_id,)).fetchone()[0]
        )
        return next(
            item
            for item in _load_controls(connection, company_id, service_date)
            if item.duty_id == duty_id
        )
