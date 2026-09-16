from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage
from transport_erp.waybill_pdf import build_waybill_pdf

router = APIRouter(prefix="/api", tags=["Waybills"])


class WaybillCandidate(BaseModel):
    duty_id: str
    duty_number: str
    service_date: str
    vehicle_label: str
    driver_label: str
    planned_departure: str
    planned_arrival: str
    released_at: str


class WaybillInput(BaseModel):
    duty_id: str
    number: str = Field(min_length=1, max_length=50)


class WaybillTrip(BaseModel):
    route_number: str
    route_name: str
    planned_departure: str
    planned_arrival: str


class WaybillResponse(BaseModel):
    id: str
    number: str
    status: str
    created_at: str
    service_date: str
    duty_id: str
    duty_number: str
    company_name: str
    company_edrpou: str | None
    vehicle_fleet_number: str
    vehicle_registration_number: str
    vehicle_make: str
    vehicle_model: str
    driver_personnel_number: str
    driver_name: str
    medical_checked_by: str | None
    medical_checked_at: str | None
    technical_checked_by: str | None
    technical_checked_at: str | None
    dispatcher_checked_by: str | None
    dispatcher_checked_at: str | None
    released_at: str
    trips: list[WaybillTrip]


def _ensure_release_storage(connection: sqlite3.Connection) -> None:
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
        "CREATE INDEX IF NOT EXISTS idx_release_controls_company "
        "ON duty_release_controls(company_id)"
    )


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local waybill API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    _ensure_release_storage(connection)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS waybills (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
            duty_id TEXT NOT NULL UNIQUE REFERENCES duties(id) ON DELETE RESTRICT,
            number TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN','CLOSED')),
            created_at TEXT NOT NULL,
            UNIQUE(company_id, number)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_waybills_company_created ON waybills(company_id, created_at)"
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


def _driver_name(row: sqlite3.Row) -> str:
    return " ".join(
        str(part)
        for part in [row["last_name"], row["first_name"], row["middle_name"]]
        if part
    )


def _load_waybill(
    connection: sqlite3.Connection, company_id: str, waybill_id: str
) -> WaybillResponse:
    row = connection.execute(
        """
        SELECT w.id, w.number, w.status, w.created_at,
               d.id AS duty_id, d.duty_number, d.service_date,
               c.name AS company_name, c.edrpou AS company_edrpou,
               v.fleet_number, v.registration_number, v.make, v.model,
               dr.personnel_number, dr.last_name, dr.first_name, dr.middle_name,
               rc.medical_checked_by, rc.medical_checked_at,
               rc.technical_checked_by, rc.technical_checked_at,
               rc.dispatcher_checked_by, rc.dispatcher_checked_at,
               rc.released_at
        FROM waybills w
        JOIN duties d ON d.id = w.duty_id
        JOIN companies c ON c.id = w.company_id
        JOIN vehicles v ON v.id = d.vehicle_id
        JOIN drivers dr ON dr.id = d.driver_id
        JOIN duty_release_controls rc ON rc.duty_id = d.id
        WHERE w.id = ? AND w.company_id = ?
        """,
        (waybill_id, company_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Шляховий лист не знайдено.")

    trip_rows = connection.execute(
        """
        SELECT r.number AS route_number, r.name AS route_name,
               t.planned_departure, t.planned_arrival
        FROM duty_trips dt
        JOIN trips t ON t.id = dt.trip_id
        JOIN routes r ON r.id = t.route_id
        WHERE dt.duty_id = ?
        ORDER BY dt.position
        """,
        (str(row["duty_id"]),),
    ).fetchall()

    return WaybillResponse(
        id=str(row["id"]),
        number=str(row["number"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        service_date=str(row["service_date"]),
        duty_id=str(row["duty_id"]),
        duty_number=str(row["duty_number"]),
        company_name=str(row["company_name"]),
        company_edrpou=(
            str(row["company_edrpou"]) if row["company_edrpou"] is not None else None
        ),
        vehicle_fleet_number=str(row["fleet_number"]),
        vehicle_registration_number=str(row["registration_number"]),
        vehicle_make=str(row["make"]),
        vehicle_model=str(row["model"]),
        driver_personnel_number=str(row["personnel_number"]),
        driver_name=_driver_name(row),
        medical_checked_by=(
            str(row["medical_checked_by"]) if row["medical_checked_by"] is not None else None
        ),
        medical_checked_at=(
            str(row["medical_checked_at"]) if row["medical_checked_at"] is not None else None
        ),
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
        released_at=str(row["released_at"]),
        trips=[
            WaybillTrip(
                route_number=str(item["route_number"]),
                route_name=str(item["route_name"]),
                planned_departure=str(item["planned_departure"]),
                planned_arrival=str(item["planned_arrival"]),
            )
            for item in trip_rows
        ],
    )


def _waybill_route_stops(connection: sqlite3.Connection, duty_id: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    route = connection.execute(
        """
        SELECT t.route_id
        FROM duty_trips dt
        JOIN trips t ON t.id = dt.trip_id
        WHERE dt.duty_id = ?
        ORDER BY dt.position
        LIMIT 1
        """,
        (duty_id,),
    ).fetchone()
    if route is None:
        return [], []
    rows = connection.execute(
        """
        SELECT s.name, s.locality, rs.position
        FROM route_stops rs
        JOIN stops s ON s.id = rs.stop_id
        WHERE rs.route_id = ?
        ORDER BY rs.position
        """,
        (str(route["route_id"]),),
    ).fetchall()
    outbound = [
        {
            "stop_name": " — ".join(
                value for value in [str(row["name"]), str(row["locality"] or "")] if value
            ),
            "arrival_time": "",
            "departure_time": "",
            "day_offset": "0",
            "point_type": "Зупинка",
            "note": "",
        }
        for row in rows
    ]
    return outbound[:15], list(reversed(outbound))[:15]


def _safe_pdf_name(number: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-zА-Яа-яІіЇїЄєҐґ._-]+", "_", number.strip())
    return cleaned or "waybill"


def _format_work_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")


def _build_pdf_data(
    connection: sqlite3.Connection, waybill: WaybillResponse
) -> dict[str, object]:
    outbound, returning = _waybill_route_stops(connection, waybill.duty_id)
    first_trip = waybill.trips[0] if waybill.trips else None
    last_trip = waybill.trips[-1] if waybill.trips else None
    route_labels = []
    for trip in waybill.trips:
        label = f"{trip.route_number} / {trip.route_name}".strip(" /")
        if label not in route_labels:
            route_labels.append(label)

    return {
        "company_name": waybill.company_name,
        "waybill_no": waybill.number,
        "waybill_series": "",
        "date": _format_work_date(waybill.service_date),
        "work_date": waybill.service_date,
        "route": ", ".join(route_labels),
        "route_code": first_trip.route_number if first_trip else "",
        "schedule_code": waybill.duty_number,
        "vehicle": " · ".join(
            value
            for value in [
                f"{waybill.vehicle_make} {waybill.vehicle_model}".strip(),
                waybill.vehicle_registration_number,
                f"гар. № {waybill.vehicle_fleet_number}",
            ]
            if value
        ),
        "driver": waybill.driver_name,
        "driver_personnel_no": waybill.driver_personnel_number,
        "planned_departure": first_trip.planned_departure if first_trip else "",
        "planned_return": last_trip.planned_arrival if last_trip else "",
        "doctor_1": waybill.medical_checked_by or "",
        "mechanic_1": waybill.technical_checked_by or "",
        "outbound_stops": outbound,
        "return_stops": returning,
        "start_direction": "outbound",
    }


@router.get("/waybill-candidates", response_model=list[WaybillCandidate])
def list_waybill_candidates(service_date: date = Query(...)) -> list[WaybillCandidate]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            """
            SELECT d.id AS duty_id, d.duty_number, d.service_date,
                   v.fleet_number, v.registration_number,
                   dr.last_name, dr.first_name, dr.middle_name,
                   MIN(t.planned_departure) AS planned_departure,
                   MAX(t.planned_arrival) AS planned_arrival,
                   rc.released_at
            FROM duties d
            JOIN vehicles v ON v.id = d.vehicle_id
            JOIN drivers dr ON dr.id = d.driver_id
            JOIN duty_trips dt ON dt.duty_id = d.id
            JOIN trips t ON t.id = dt.trip_id
            JOIN duty_release_controls rc ON rc.duty_id = d.id AND rc.released_at IS NOT NULL
            LEFT JOIN waybills w ON w.duty_id = d.id
            WHERE d.company_id = ? AND d.service_date = ? AND w.id IS NULL
            GROUP BY d.id
            ORDER BY planned_departure, d.duty_number COLLATE NOCASE
            """,
            (company_id, service_date.isoformat()),
        ).fetchall()

    return [
        WaybillCandidate(
            duty_id=str(row["duty_id"]),
            duty_number=str(row["duty_number"]),
            service_date=str(row["service_date"]),
            vehicle_label=f"{row['fleet_number']} — {row['registration_number']}",
            driver_label=_driver_name(row),
            planned_departure=str(row["planned_departure"]),
            planned_arrival=str(row["planned_arrival"]),
            released_at=str(row["released_at"]),
        )
        for row in rows
    ]


@router.get("/waybills", response_model=list[WaybillResponse])
def list_waybills(service_date: date = Query(...)) -> list[WaybillResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        ids = connection.execute(
            """
            SELECT w.id
            FROM waybills w
            JOIN duties d ON d.id = w.duty_id
            WHERE w.company_id = ? AND d.service_date = ?
            ORDER BY w.number COLLATE NOCASE
            """,
            (company_id, service_date.isoformat()),
        ).fetchall()
        return [_load_waybill(connection, company_id, str(row["id"])) for row in ids]


@router.get("/waybills/{waybill_id}", response_model=WaybillResponse)
def get_waybill(waybill_id: str) -> WaybillResponse:
    with _connection() as connection:
        return _load_waybill(connection, _company_id(connection), waybill_id)


@router.get("/waybills/{waybill_id}/pdf", response_class=FileResponse)
def get_waybill_pdf(waybill_id: str) -> FileResponse:
    settings = get_settings()
    with _connection() as connection:
        waybill = _load_waybill(connection, _company_id(connection), waybill_id)
        data = _build_pdf_data(connection, waybill)

    work_date = datetime.strptime(waybill.service_date, "%Y-%m-%d")
    output_dir = (
        settings.resolved_documents_dir
        / "waybills"
        / work_date.strftime("%Y")
        / work_date.strftime("%m")
    )
    output_path = output_dir / f"Waybill_{_safe_pdf_name(waybill.number)}.pdf"
    build_waybill_pdf(None, output_path, data)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_path.name,
    )


@router.post("/waybills", response_model=WaybillResponse, status_code=201)
def create_waybill(payload: WaybillInput) -> WaybillResponse:
    waybill_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    try:
        with _connection(write=True) as connection:
            company_id = _company_id(connection)
            candidate = connection.execute(
                """
                SELECT d.id
                FROM duties d
                JOIN duty_release_controls rc ON rc.duty_id = d.id
                WHERE d.id = ? AND d.company_id = ? AND rc.released_at IS NOT NULL
                """,
                (payload.duty_id, company_id),
            ).fetchone()
            if candidate is None:
                raise HTTPException(
                    status_code=409,
                    detail="Шляховий лист можна створити тільки для випущеного наряду.",
                )

            connection.execute(
                """
                INSERT INTO waybills(id, company_id, duty_id, number, status, created_at)
                VALUES (?, ?, ?, ?, 'OPEN', ?)
                """,
                (waybill_id, company_id, payload.duty_id, payload.number.strip(), now),
            )
            return _load_waybill(connection, company_id, waybill_id)
    except sqlite3.IntegrityError as exc:
        message = str(exc).lower()
        if "duty_id" in message:
            detail = "Для цього наряду шляховий лист уже створено."
        else:
            detail = "Шляховий лист з таким номером уже існує."
        raise HTTPException(status_code=409, detail=detail) from exc
