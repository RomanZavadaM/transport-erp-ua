from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from transport_erp.config import get_settings
from transport_erp.fuel import ensure_fuel_storage
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Fuel"])


class FuelHistoryItem(BaseModel):
    id: str
    waybill_id: str
    waybill_number: str
    service_date: str
    driver_name: str
    fuel_start_liters: float
    fuel_issued_liters: float
    fuel_end_liters: float
    fuel_consumed_liters: float
    created_at: str


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local fuel API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    ensure_fuel_storage(connection)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _company_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = 'company_id'").fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Підприємство не ініціалізоване.")
    return str(row["value"])


@router.get("/vehicles/{vehicle_id}/fuel-history", response_model=list[FuelHistoryItem])
def vehicle_fuel_history(vehicle_id: str) -> list[FuelHistoryItem]:
    with _connection() as connection:
        vehicle = connection.execute(
            "SELECT id FROM vehicles WHERE id = ? AND company_id = ?",
            (vehicle_id, _company_id(connection)),
        ).fetchone()
        if vehicle is None:
            raise HTTPException(status_code=404, detail="Автобус не знайдено.")

        rows = connection.execute(
            """
            SELECT f.id, f.waybill_id, w.number AS waybill_number,
                   f.service_date,
                   dr.last_name, dr.first_name, dr.middle_name,
                   f.fuel_start_liters, f.fuel_issued_liters,
                   f.fuel_end_liters, f.fuel_consumed_liters,
                   f.created_at
            FROM fuel_waybill_history f
            JOIN waybills w ON w.id = f.waybill_id
            LEFT JOIN drivers dr ON dr.id = f.driver_id
            WHERE f.vehicle_id = ?
            ORDER BY f.service_date DESC, f.created_at DESC
            """,
            (vehicle_id,),
        ).fetchall()

    return [
        FuelHistoryItem(
            id=str(row["id"]),
            waybill_id=str(row["waybill_id"]),
            waybill_number=str(row["waybill_number"]),
            service_date=str(row["service_date"]),
            driver_name=" ".join(
                str(value)
                for value in [row["last_name"], row["first_name"], row["middle_name"]]
                if value
            ),
            fuel_start_liters=float(row["fuel_start_liters"]),
            fuel_issued_liters=float(row["fuel_issued_liters"]),
            fuel_end_liters=float(row["fuel_end_liters"]),
            fuel_consumed_liters=float(row["fuel_consumed_liters"]),
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]
