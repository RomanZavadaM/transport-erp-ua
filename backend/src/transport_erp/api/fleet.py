from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Iterator, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(tags=["Fleet & Drivers"])

VehicleStatus = Literal["ACTIVE", "SUSPENDED", "REPAIR", "DECOMMISSIONED"]
DriverStatus = Literal["ACTIVE", "LEAVE", "SICK", "SUSPENDED", "TERMINATED"]


class VehicleInput(BaseModel):
    fleet_number: str = Field(min_length=1, max_length=30)
    registration_number: str = Field(min_length=1, max_length=20)
    vin: str | None = Field(default=None, max_length=32)
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1950, le=2100)
    lifecycle_status: VehicleStatus = "ACTIVE"


class VehicleResponse(VehicleInput):
    id: str
    row_version: int


class DriverInput(BaseModel):
    personnel_number: str = Field(min_length=1, max_length=30)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=40)
    employment_status: DriverStatus = "ACTIVE"


class DriverResponse(DriverInput):
    id: str
    row_version: int


def _require_local() -> None:
    if get_settings().deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local fleet API is disabled")


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    _require_local()
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _company_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = 'company_id'").fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Local company is not initialized")
    return str(row["value"])


def _vehicle_from_row(row: sqlite3.Row) -> VehicleResponse:
    return VehicleResponse(
        id=str(row["id"]),
        fleet_number=str(row["fleet_number"]),
        registration_number=str(row["registration_number"]),
        vin=str(row["vin"]) if row["vin"] is not None else None,
        make=str(row["make"]),
        model=str(row["model"]),
        year=int(row["year"]) if row["year"] is not None else None,
        lifecycle_status=str(row["lifecycle_status"]),
        row_version=int(row["row_version"]),
    )


def _driver_from_row(row: sqlite3.Row) -> DriverResponse:
    return DriverResponse(
        id=str(row["id"]),
        personnel_number=str(row["personnel_number"]),
        last_name=str(row["last_name"]),
        first_name=str(row["first_name"]),
        middle_name=str(row["middle_name"]) if row["middle_name"] is not None else None,
        phone=str(row["phone"]) if row["phone"] is not None else None,
        employment_status=str(row["employment_status"]),
        row_version=int(row["row_version"]),
    )


@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles() -> list[VehicleResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            """
            SELECT id, fleet_number, registration_number, vin, make, model, year,
                   lifecycle_status, row_version
            FROM vehicles
            WHERE company_id = ?
            ORDER BY fleet_number COLLATE NOCASE
            """,
            (company_id,),
        ).fetchall()
    return [_vehicle_from_row(row) for row in rows]


@router.post("/vehicles", response_model=VehicleResponse, status_code=201)
def create_vehicle(payload: VehicleInput) -> VehicleResponse:
    now = datetime.now(UTC).isoformat()
    vehicle_id = str(uuid4())
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            connection.execute(
                """
                INSERT INTO vehicles (
                    id, company_id, fleet_number, registration_number, vin,
                    make, model, year, lifecycle_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vehicle_id,
                    company_id,
                    payload.fleet_number.strip(),
                    payload.registration_number.strip().upper(),
                    payload.vin.strip().upper() if payload.vin else None,
                    payload.make.strip(),
                    payload.model.strip(),
                    payload.year,
                    payload.lifecycle_status,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT id, fleet_number, registration_number, vin, make, model, year,
                       lifecycle_status, row_version
                FROM vehicles WHERE id = ?
                """,
                (vehicle_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Автобус з таким гаражним, реєстраційним номером або VIN уже існує.",
        ) from exc
    if row is None:
        raise HTTPException(status_code=500, detail="Vehicle was not created")
    return _vehicle_from_row(row)


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str, payload: VehicleInput) -> VehicleResponse:
    now = datetime.now(UTC).isoformat()
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            cursor = connection.execute(
                """
                UPDATE vehicles
                SET fleet_number = ?, registration_number = ?, vin = ?, make = ?, model = ?,
                    year = ?, lifecycle_status = ?, updated_at = ?, row_version = row_version + 1
                WHERE id = ? AND company_id = ?
                """,
                (
                    payload.fleet_number.strip(),
                    payload.registration_number.strip().upper(),
                    payload.vin.strip().upper() if payload.vin else None,
                    payload.make.strip(),
                    payload.model.strip(),
                    payload.year,
                    payload.lifecycle_status,
                    now,
                    vehicle_id,
                    company_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Автобус не знайдено.")
            row = connection.execute(
                """
                SELECT id, fleet_number, registration_number, vin, make, model, year,
                       lifecycle_status, row_version
                FROM vehicles WHERE id = ?
                """,
                (vehicle_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Автобус з таким гаражним, реєстраційним номером або VIN уже існує.",
        ) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Автобус не знайдено.")
    return _vehicle_from_row(row)


@router.get("/drivers", response_model=list[DriverResponse])
def list_drivers() -> list[DriverResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            """
            SELECT id, personnel_number, last_name, first_name, middle_name, phone,
                   employment_status, row_version
            FROM drivers
            WHERE company_id = ?
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
            """,
            (company_id,),
        ).fetchall()
    return [_driver_from_row(row) for row in rows]


@router.post("/drivers", response_model=DriverResponse, status_code=201)
def create_driver(payload: DriverInput) -> DriverResponse:
    now = datetime.now(UTC).isoformat()
    driver_id = str(uuid4())
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            connection.execute(
                """
                INSERT INTO drivers (
                    id, company_id, personnel_number, last_name, first_name, middle_name,
                    phone, employment_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    driver_id,
                    company_id,
                    payload.personnel_number.strip(),
                    payload.last_name.strip(),
                    payload.first_name.strip(),
                    payload.middle_name.strip() if payload.middle_name else None,
                    payload.phone.strip() if payload.phone else None,
                    payload.employment_status,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT id, personnel_number, last_name, first_name, middle_name, phone,
                       employment_status, row_version
                FROM drivers WHERE id = ?
                """,
                (driver_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Водій з таким табельним номером уже існує.",
        ) from exc
    if row is None:
        raise HTTPException(status_code=500, detail="Driver was not created")
    return _driver_from_row(row)


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: str, payload: DriverInput) -> DriverResponse:
    now = datetime.now(UTC).isoformat()
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            cursor = connection.execute(
                """
                UPDATE drivers
                SET personnel_number = ?, last_name = ?, first_name = ?, middle_name = ?,
                    phone = ?, employment_status = ?, updated_at = ?, row_version = row_version + 1
                WHERE id = ? AND company_id = ?
                """,
                (
                    payload.personnel_number.strip(),
                    payload.last_name.strip(),
                    payload.first_name.strip(),
                    payload.middle_name.strip() if payload.middle_name else None,
                    payload.phone.strip() if payload.phone else None,
                    payload.employment_status,
                    now,
                    driver_id,
                    company_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Водія не знайдено.")
            row = connection.execute(
                """
                SELECT id, personnel_number, last_name, first_name, middle_name, phone,
                       employment_status, row_version
                FROM drivers WHERE id = ?
                """,
                (driver_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Водій з таким табельним номером уже існує.",
        ) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Водія не знайдено.")
    return _driver_from_row(row)
