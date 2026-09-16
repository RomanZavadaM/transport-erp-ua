from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import cast
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Fleet details"])


class DocumentInput(BaseModel):
    document_type: str = Field(min_length=1, max_length=100)
    number: str = Field(min_length=1, max_length=100)
    valid_until: date | None = None
    note: str | None = Field(default=None, max_length=500)


class DocumentResponse(DocumentInput):
    id: str


class OdometerInput(BaseModel):
    reading_km: int = Field(ge=0)
    recorded_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)


class OdometerResponse(BaseModel):
    id: str
    reading_km: int
    recorded_at: datetime
    note: str | None


class VehicleDetailsResponse(BaseModel):
    id: str
    fleet_number: str
    registration_number: str
    vin: str | None
    make: str
    model: str
    year: int | None
    lifecycle_status: str
    documents: list[DocumentResponse]
    odometer: list[OdometerResponse]


class DriverDetailsResponse(BaseModel):
    id: str
    personnel_number: str
    last_name: str
    first_name: str
    middle_name: str | None
    phone: str | None
    employment_status: str
    documents: list[DocumentResponse]


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local details API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS vehicle_documents (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            document_type TEXT NOT NULL,
            number TEXT NOT NULL,
            valid_until TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS driver_documents (
            id TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            document_type TEXT NOT NULL,
            number TEXT NOT NULL,
            valid_until TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS odometer_readings (
            id TEXT PRIMARY KEY,
            vehicle_id TEXT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            reading_km INTEGER NOT NULL CHECK (reading_km >= 0),
            recorded_at TEXT NOT NULL,
            note TEXT
        );
        """
    )
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
        raise HTTPException(status_code=500, detail="Підприємство не ініціалізоване.")
    return str(row["value"])


def _documents(
    connection: sqlite3.Connection,
    table: str,
    owner_field: str,
    owner_id: str,
) -> list[DocumentResponse]:
    rows = connection.execute(
        f"""
        SELECT id, document_type, number, valid_until, note
        FROM {table}
        WHERE {owner_field} = ?
        ORDER BY valid_until IS NULL, valid_until, document_type COLLATE NOCASE
        """,
        (owner_id,),
    ).fetchall()
    return [
        DocumentResponse(
            id=str(row["id"]),
            document_type=str(row["document_type"]),
            number=str(row["number"]),
            valid_until=date.fromisoformat(str(row["valid_until"])) if row["valid_until"] else None,
            note=str(row["note"]) if row["note"] is not None else None,
        )
        for row in rows
    ]


def _odometer(connection: sqlite3.Connection, vehicle_id: str) -> list[OdometerResponse]:
    rows = connection.execute(
        """
        SELECT id, reading_km, recorded_at, note
        FROM odometer_readings
        WHERE vehicle_id = ?
        ORDER BY recorded_at DESC
        """,
        (vehicle_id,),
    ).fetchall()
    return [
        OdometerResponse(
            id=str(row["id"]),
            reading_km=int(row["reading_km"]),
            recorded_at=datetime.fromisoformat(str(row["recorded_at"])),
            note=str(row["note"]) if row["note"] is not None else None,
        )
        for row in rows
    ]


def _require_vehicle(connection: sqlite3.Connection, vehicle_id: str) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT id, fleet_number, registration_number, vin, make, model, year, lifecycle_status
        FROM vehicles WHERE id = ? AND company_id = ?
        """,
        (vehicle_id, _company_id(connection)),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Автобус не знайдено.")
    return cast(sqlite3.Row, row)


def _require_driver(connection: sqlite3.Connection, driver_id: str) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT id, personnel_number, last_name, first_name, middle_name, phone, employment_status
        FROM drivers WHERE id = ? AND company_id = ?
        """,
        (driver_id, _company_id(connection)),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Водія не знайдено.")
    return cast(sqlite3.Row, row)


@router.get("/vehicles/{vehicle_id}/details", response_model=VehicleDetailsResponse)
def vehicle_details(vehicle_id: str) -> VehicleDetailsResponse:
    with _connection() as connection:
        row = _require_vehicle(connection, vehicle_id)
        return VehicleDetailsResponse(
            id=str(row["id"]),
            fleet_number=str(row["fleet_number"]),
            registration_number=str(row["registration_number"]),
            vin=str(row["vin"]) if row["vin"] is not None else None,
            make=str(row["make"]),
            model=str(row["model"]),
            year=int(row["year"]) if row["year"] is not None else None,
            lifecycle_status=str(row["lifecycle_status"]),
            documents=_documents(connection, "vehicle_documents", "vehicle_id", vehicle_id),
            odometer=_odometer(connection, vehicle_id),
        )


@router.post(
    "/vehicles/{vehicle_id}/documents", response_model=DocumentResponse, status_code=201
)
def add_vehicle_document(vehicle_id: str, payload: DocumentInput) -> DocumentResponse:
    document_id = str(uuid4())
    with _connection() as connection:
        _require_vehicle(connection, vehicle_id)
        connection.execute(
            """
            INSERT INTO vehicle_documents(
                id, vehicle_id, document_type, number, valid_until, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                vehicle_id,
                payload.document_type.strip(),
                payload.number.strip(),
                payload.valid_until.isoformat() if payload.valid_until else None,
                payload.note.strip() if payload.note else None,
                datetime.now(UTC).isoformat(),
            ),
        )
    return DocumentResponse(id=document_id, **payload.model_dump())


@router.post(
    "/vehicles/{vehicle_id}/odometer", response_model=OdometerResponse, status_code=201
)
def add_odometer(vehicle_id: str, payload: OdometerInput) -> OdometerResponse:
    reading_id = str(uuid4())
    recorded_at = payload.recorded_at or datetime.now(UTC)
    with _connection() as connection:
        _require_vehicle(connection, vehicle_id)
        latest = connection.execute(
            """
            SELECT reading_km FROM odometer_readings
            WHERE vehicle_id = ? ORDER BY recorded_at DESC LIMIT 1
            """,
            (vehicle_id,),
        ).fetchone()
        if latest is not None and payload.reading_km < int(latest["reading_km"]):
            raise HTTPException(
                status_code=400,
                detail="Нове показання одометра не може бути меншим за попереднє.",
            )
        connection.execute(
            """
            INSERT INTO odometer_readings(id, vehicle_id, reading_km, recorded_at, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                reading_id,
                vehicle_id,
                payload.reading_km,
                recorded_at.isoformat(),
                payload.note.strip() if payload.note else None,
            ),
        )
    return OdometerResponse(
        id=reading_id,
        reading_km=payload.reading_km,
        recorded_at=recorded_at,
        note=payload.note,
    )


@router.get("/drivers/{driver_id}/details", response_model=DriverDetailsResponse)
def driver_details(driver_id: str) -> DriverDetailsResponse:
    with _connection() as connection:
        row = _require_driver(connection, driver_id)
        return DriverDetailsResponse(
            id=str(row["id"]),
            personnel_number=str(row["personnel_number"]),
            last_name=str(row["last_name"]),
            first_name=str(row["first_name"]),
            middle_name=str(row["middle_name"]) if row["middle_name"] is not None else None,
            phone=str(row["phone"]) if row["phone"] is not None else None,
            employment_status=str(row["employment_status"]),
            documents=_documents(connection, "driver_documents", "driver_id", driver_id),
        )


@router.post(
    "/drivers/{driver_id}/documents", response_model=DocumentResponse, status_code=201
)
def add_driver_document(driver_id: str, payload: DocumentInput) -> DocumentResponse:
    document_id = str(uuid4())
    with _connection() as connection:
        _require_driver(connection, driver_id)
        connection.execute(
            """
            INSERT INTO driver_documents(
                id, driver_id, document_type, number, valid_until, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                driver_id,
                payload.document_type.strip(),
                payload.number.strip(),
                payload.valid_until.isoformat() if payload.valid_until else None,
                payload.note.strip() if payload.note else None,
                datetime.now(UTC).isoformat(),
            ),
        )
    return DocumentResponse(id=document_id, **payload.model_dump())
