from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4


def ensure_fuel_storage(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS fuel_waybill_history (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
            driver_id TEXT REFERENCES drivers(id) ON DELETE SET NULL,
            waybill_id TEXT NOT NULL UNIQUE REFERENCES waybills(id) ON DELETE RESTRICT,
            service_date TEXT NOT NULL,
            fuel_start_liters REAL NOT NULL CHECK (fuel_start_liters >= 0),
            fuel_issued_liters REAL NOT NULL CHECK (fuel_issued_liters >= 0),
            fuel_end_liters REAL NOT NULL CHECK (fuel_end_liters >= 0),
            fuel_consumed_liters REAL NOT NULL CHECK (fuel_consumed_liters >= 0),
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fuel_waybill_history_vehicle_date
        ON fuel_waybill_history(vehicle_id, service_date, created_at)
        """
    )


def record_waybill_fuel_history(
    connection: sqlite3.Connection,
    *,
    vehicle_id: str,
    driver_id: str | None,
    waybill_id: str,
    service_date: str,
    fuel_start_liters: float | None,
    fuel_issued_liters: float | None,
    fuel_end_liters: float | None,
) -> None:
    if (
        fuel_start_liters is None
        or fuel_issued_liters is None
        or fuel_end_liters is None
    ):
        return

    consumed = round(fuel_start_liters + fuel_issued_liters - fuel_end_liters, 2)
    if consumed < 0:
        raise ValueError("Fuel consumption cannot be negative")

    ensure_fuel_storage(connection)
    connection.execute(
        """
        INSERT OR IGNORE INTO fuel_waybill_history(
            id, vehicle_id, driver_id, waybill_id, service_date,
            fuel_start_liters, fuel_issued_liters, fuel_end_liters,
            fuel_consumed_liters, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            vehicle_id,
            driver_id,
            waybill_id,
            service_date,
            fuel_start_liters,
            fuel_issued_liters,
            fuel_end_liters,
            consumed,
            datetime.now(UTC).isoformat(),
        ),
    )
