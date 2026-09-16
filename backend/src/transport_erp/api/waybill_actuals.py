from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Waybill actuals"])


class WaybillActualInput(BaseModel):
    actual_departure: datetime | None = None
    actual_return: datetime | None = None
    odometer_start: int | None = Field(default=None, ge=0)
    odometer_end: int | None = Field(default=None, ge=0)
    fuel_start_liters: float | None = Field(default=None, ge=0)
    fuel_issued_liters: float | None = Field(default=None, ge=0)
    fuel_end_liters: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=1000)


class WaybillActualResponse(WaybillActualInput):
    waybill_id: str
    status: str
    distance_km: int | None
    fuel_consumed_liters: float | None
    updated_at: datetime | None
    closed_at: datetime | None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: object) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    return datetime.fromisoformat(str(value))


def _calculated_distance(start: int | None, end: int | None) -> int | None:
    if start is None or end is None:
        return None
    return end - start


def _calculated_fuel(start: float | None, issued: float | None, end: float | None) -> float | None:
    if start is None or issued is None or end is None:
        return None
    return round(start + issued - end, 2)


def _validate(payload: WaybillActualInput) -> None:
    if (
        payload.odometer_start is not None
        and payload.odometer_end is not None
        and payload.odometer_end < payload.odometer_start
    ):
        raise HTTPException(
            status_code=400,
            detail="Показання одометра при поверненні не може бути меншим за показання при виїзді.",
        )
    if (
        payload.actual_departure is not None
        and payload.actual_return is not None
        and payload.actual_return < payload.actual_departure
    ):
        raise HTTPException(
            status_code=400,
            detail="Фактичне повернення не може бути раніше фактичного виїзду.",
        )
    fuel = _calculated_fuel(
        payload.fuel_start_liters,
        payload.fuel_issued_liters,
        payload.fuel_end_liters,
    )
    if fuel is not None and fuel < 0:
        raise HTTPException(
            status_code=400,
            detail="Розрахована витрата пального не може бути від’ємною.",
        )


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local waybill actuals API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS waybill_actuals (
            waybill_id TEXT PRIMARY KEY REFERENCES waybills(id) ON DELETE CASCADE,
            actual_departure TEXT,
            actual_return TEXT,
            odometer_start INTEGER CHECK (odometer_start IS NULL OR odometer_start >= 0),
            odometer_end INTEGER CHECK (odometer_end IS NULL OR odometer_end >= 0),
            fuel_start_liters REAL CHECK (fuel_start_liters IS NULL OR fuel_start_liters >= 0),
            fuel_issued_liters REAL CHECK (fuel_issued_liters IS NULL OR fuel_issued_liters >= 0),
            fuel_end_liters REAL CHECK (fuel_end_liters IS NULL OR fuel_end_liters >= 0),
            note TEXT,
            updated_at TEXT NOT NULL,
            closed_at TEXT,
            CHECK (
                odometer_start IS NULL OR odometer_end IS NULL OR odometer_end >= odometer_start
            )
        )
        """
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


def _require_waybill(connection: sqlite3.Connection, waybill_id: str) -> sqlite3.Row:
    try:
        row = connection.execute(
            """
            SELECT w.id, w.number, w.status, w.duty_id,
                   d.vehicle_id, d.driver_id, d.service_date
            FROM waybills w
            JOIN duties d ON d.id = w.duty_id
            WHERE w.id = ?
            """,
            (waybill_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        raise HTTPException(status_code=404, detail="Шляховий лист не знайдено.") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Шляховий лист не знайдено.")
    return row


def _load_actuals(connection: sqlite3.Connection, waybill_id: str) -> WaybillActualResponse:
    waybill = _require_waybill(connection, waybill_id)
    row = connection.execute(
        """
        SELECT actual_departure, actual_return, odometer_start, odometer_end,
               fuel_start_liters, fuel_issued_liters, fuel_end_liters,
               note, updated_at, closed_at
        FROM waybill_actuals
        WHERE waybill_id = ?
        """,
        (waybill_id,),
    ).fetchone()
    if row is None:
        return WaybillActualResponse(
            waybill_id=waybill_id,
            status=str(waybill["status"]),
            actual_departure=None,
            actual_return=None,
            odometer_start=None,
            odometer_end=None,
            fuel_start_liters=None,
            fuel_issued_liters=None,
            fuel_end_liters=None,
            note=None,
            distance_km=None,
            fuel_consumed_liters=None,
            updated_at=None,
            closed_at=None,
        )

    odometer_start = int(row["odometer_start"]) if row["odometer_start"] is not None else None
    odometer_end = int(row["odometer_end"]) if row["odometer_end"] is not None else None
    fuel_start = float(row["fuel_start_liters"]) if row["fuel_start_liters"] is not None else None
    fuel_issued = (
        float(row["fuel_issued_liters"]) if row["fuel_issued_liters"] is not None else None
    )
    fuel_end = float(row["fuel_end_liters"]) if row["fuel_end_liters"] is not None else None
    return WaybillActualResponse(
        waybill_id=waybill_id,
        status=str(waybill["status"]),
        actual_departure=_parse_datetime(row["actual_departure"]),
        actual_return=_parse_datetime(row["actual_return"]),
        odometer_start=odometer_start,
        odometer_end=odometer_end,
        fuel_start_liters=fuel_start,
        fuel_issued_liters=fuel_issued,
        fuel_end_liters=fuel_end,
        note=str(row["note"]) if row["note"] is not None else None,
        distance_km=_calculated_distance(odometer_start, odometer_end),
        fuel_consumed_liters=_calculated_fuel(fuel_start, fuel_issued, fuel_end),
        updated_at=_parse_datetime(row["updated_at"]),
        closed_at=_parse_datetime(row["closed_at"]),
    )


@router.get("/waybills/{waybill_id}/actuals", response_model=WaybillActualResponse)
def get_waybill_actuals(waybill_id: str) -> WaybillActualResponse:
    with _connection() as connection:
        return _load_actuals(connection, waybill_id)


@router.put("/waybills/{waybill_id}/actuals", response_model=WaybillActualResponse)
def save_waybill_actuals(
    waybill_id: str,
    payload: WaybillActualInput,
) -> WaybillActualResponse:
    _validate(payload)
    with _connection(write=True) as connection:
        waybill = _require_waybill(connection, waybill_id)
        if str(waybill["status"]) == "CLOSED":
            raise HTTPException(status_code=409, detail="Закритий шляховий лист не редагується.")
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """
            INSERT INTO waybill_actuals(
                waybill_id, actual_departure, actual_return,
                odometer_start, odometer_end,
                fuel_start_liters, fuel_issued_liters, fuel_end_liters,
                note, updated_at, closed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(waybill_id) DO UPDATE SET
                actual_departure = excluded.actual_departure,
                actual_return = excluded.actual_return,
                odometer_start = excluded.odometer_start,
                odometer_end = excluded.odometer_end,
                fuel_start_liters = excluded.fuel_start_liters,
                fuel_issued_liters = excluded.fuel_issued_liters,
                fuel_end_liters = excluded.fuel_end_liters,
                note = excluded.note,
                updated_at = excluded.updated_at
            """,
            (
                waybill_id,
                _iso(payload.actual_departure),
                _iso(payload.actual_return),
                payload.odometer_start,
                payload.odometer_end,
                payload.fuel_start_liters,
                payload.fuel_issued_liters,
                payload.fuel_end_liters,
                payload.note.strip() if payload.note else None,
                now,
            ),
        )
        return _load_actuals(connection, waybill_id)


def _ensure_odometer_storage(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS odometer_readings (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            reading_km INTEGER NOT NULL CHECK (reading_km >= 0),
            recorded_at TEXT NOT NULL,
            note TEXT
        )
        """
    )


def _latest_odometer(connection: sqlite3.Connection, vehicle_id: str) -> int | None:
    _ensure_odometer_storage(connection)
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


@router.post("/waybills/{waybill_id}/close", response_model=WaybillActualResponse)
def close_waybill(waybill_id: str) -> WaybillActualResponse:
    with _connection(write=True) as connection:
        waybill = _require_waybill(connection, waybill_id)
        if str(waybill["status"]) == "CLOSED":
            raise HTTPException(status_code=409, detail="Шляховий лист уже закрито.")

        actuals = _load_actuals(connection, waybill_id)
        if (
            actuals.actual_departure is None
            or actuals.actual_return is None
            or actuals.odometer_start is None
            or actuals.odometer_end is None
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Для закриття потрібні фактичний виїзд, фактичне повернення "
                    "та показання одометра на виїзді і поверненні."
                ),
            )

        latest = _latest_odometer(connection, str(waybill["vehicle_id"]))
        if latest is not None and actuals.odometer_start < latest:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Показання одометра при виїзді менше останнього збереженого "
                    f"показання ({latest} км)."
                ),
            )

        note = f"Шляхівка {waybill['number']}"
        connection.execute(
            """
            INSERT INTO odometer_readings(id, vehicle_id, reading_km, recorded_at, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                str(waybill["vehicle_id"]),
                actuals.odometer_start,
                actuals.actual_departure.isoformat(),
                f"{note} — виїзд",
            ),
        )
        connection.execute(
            """
            INSERT INTO odometer_readings(id, vehicle_id, reading_km, recorded_at, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                str(waybill["vehicle_id"]),
                actuals.odometer_end,
                actuals.actual_return.isoformat(),
                f"{note} — повернення",
            ),
        )

        closed_at = datetime.now(UTC).isoformat()
        connection.execute("UPDATE waybills SET status = 'CLOSED' WHERE id = ?", (waybill_id,))
        connection.execute(
            "UPDATE waybill_actuals SET closed_at = ?, updated_at = ? WHERE waybill_id = ?",
            (closed_at, closed_at, waybill_id),
        )
        connection.execute(
            "UPDATE duties SET status = 'COMPLETED' WHERE id = ?",
            (str(waybill["duty_id"]),),
        )
        connection.execute(
            """
            UPDATE trips
            SET status = 'COMPLETED'
            WHERE id IN (SELECT trip_id FROM duty_trips WHERE duty_id = ?)
            """,
            (str(waybill["duty_id"]),),
        )
        return _load_actuals(connection, waybill_id)
