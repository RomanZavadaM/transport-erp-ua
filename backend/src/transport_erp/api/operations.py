from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Operations"])


class ScheduleInput(BaseModel):
    route_id: str
    departure_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    arrival_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    active: bool = True


class ScheduleResponse(BaseModel):
    id: str
    route_id: str
    route_number: str
    route_name: str
    departure_time: str
    arrival_time: str
    active: bool


class TripGenerationInput(BaseModel):
    service_date: date


class TripResponse(BaseModel):
    id: str
    schedule_id: str
    route_id: str
    route_number: str
    route_name: str
    service_date: str
    planned_departure: str
    planned_arrival: str
    status: str
    duty_id: str | None
    duty_number: str | None


class DutyInput(BaseModel):
    service_date: date
    duty_number: str = Field(min_length=1, max_length=30)
    vehicle_id: str
    driver_id: str
    trip_ids: list[str] = Field(min_length=1)


class DutyTripResponse(BaseModel):
    id: str
    route_number: str
    route_name: str
    planned_departure: str
    planned_arrival: str


class DutyResponse(BaseModel):
    id: str
    service_date: str
    duty_number: str
    vehicle_id: str
    vehicle_label: str
    driver_id: str
    driver_label: str
    status: str
    trips: list[DutyTripResponse]


@contextmanager
def _connection(*, write: bool = False) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local operations API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
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


def _validated_time(value: str, label: str) -> str:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Невірний час: {label}.") from exc
    return parsed.strftime("%H:%M")


def _schedule_from_row(row: sqlite3.Row) -> ScheduleResponse:
    return ScheduleResponse(
        id=str(row["id"]),
        route_id=str(row["route_id"]),
        route_number=str(row["route_number"]),
        route_name=str(row["route_name"]),
        departure_time=str(row["departure_time"]),
        arrival_time=str(row["arrival_time"]),
        active=bool(row["active"]),
    )


def _trip_from_row(row: sqlite3.Row) -> TripResponse:
    return TripResponse(
        id=str(row["id"]),
        schedule_id=str(row["schedule_id"]),
        route_id=str(row["route_id"]),
        route_number=str(row["route_number"]),
        route_name=str(row["route_name"]),
        service_date=str(row["service_date"]),
        planned_departure=str(row["planned_departure"]),
        planned_arrival=str(row["planned_arrival"]),
        status=str(row["status"]),
        duty_id=str(row["duty_id"]) if row["duty_id"] is not None else None,
        duty_number=str(row["duty_number"]) if row["duty_number"] is not None else None,
    )


def _load_trips(connection: sqlite3.Connection, company_id: str, service_date: str) -> list[TripResponse]:
    rows = connection.execute(
        """
        SELECT t.id, t.schedule_id, t.route_id, r.number AS route_number,
               r.name AS route_name, t.service_date, t.planned_departure,
               t.planned_arrival, t.status, d.id AS duty_id, d.duty_number
        FROM trips t
        JOIN routes r ON r.id = t.route_id
        LEFT JOIN duty_trips dt ON dt.trip_id = t.id
        LEFT JOIN duties d ON d.id = dt.duty_id AND d.status <> 'CANCELLED'
        WHERE t.company_id = ? AND t.service_date = ?
        ORDER BY t.planned_departure, r.number COLLATE NOCASE
        """,
        (company_id, service_date),
    ).fetchall()
    return [_trip_from_row(row) for row in rows]


def _load_duty(connection: sqlite3.Connection, company_id: str, duty_id: str) -> DutyResponse:
    row = connection.execute(
        """
        SELECT d.id, d.service_date, d.duty_number, d.vehicle_id, d.driver_id, d.status,
               v.fleet_number, v.registration_number,
               dr.last_name, dr.first_name, dr.middle_name
        FROM duties d
        JOIN vehicles v ON v.id = d.vehicle_id
        JOIN drivers dr ON dr.id = d.driver_id
        WHERE d.id = ? AND d.company_id = ?
        """,
        (duty_id, company_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Наряд не знайдено.")
    trip_rows = connection.execute(
        """
        SELECT t.id, r.number AS route_number, r.name AS route_name,
               t.planned_departure, t.planned_arrival
        FROM duty_trips dt
        JOIN trips t ON t.id = dt.trip_id
        JOIN routes r ON r.id = t.route_id
        WHERE dt.duty_id = ?
        ORDER BY dt.position
        """,
        (duty_id,),
    ).fetchall()
    middle = f" {row['middle_name']}" if row["middle_name"] else ""
    return DutyResponse(
        id=str(row["id"]),
        service_date=str(row["service_date"]),
        duty_number=str(row["duty_number"]),
        vehicle_id=str(row["vehicle_id"]),
        vehicle_label=f"{row['fleet_number']} — {row['registration_number']}",
        driver_id=str(row["driver_id"]),
        driver_label=f"{row['last_name']} {row['first_name']}{middle}",
        status=str(row["status"]),
        trips=[
            DutyTripResponse(
                id=str(item["id"]),
                route_number=str(item["route_number"]),
                route_name=str(item["route_name"]),
                planned_departure=str(item["planned_departure"]),
                planned_arrival=str(item["planned_arrival"]),
            )
            for item in trip_rows
        ],
    )


def _overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    return start_a < end_b and start_b < end_a


def _assert_resource_available(
    connection: sqlite3.Connection,
    company_id: str,
    service_date: str,
    column: str,
    resource_id: str,
    selected: list[sqlite3.Row],
    label: str,
) -> None:
    if column not in {"vehicle_id", "driver_id"}:
        raise ValueError("Unsupported resource column")
    existing = connection.execute(
        f"""
        SELECT t.planned_departure, t.planned_arrival
        FROM duties d
        JOIN duty_trips dt ON dt.duty_id = d.id
        JOIN trips t ON t.id = dt.trip_id
        WHERE d.company_id = ? AND d.service_date = ?
          AND d.{column} = ? AND d.status <> 'CANCELLED'
        """,
        (company_id, service_date, resource_id),
    ).fetchall()
    for candidate in selected:
        for assigned in existing:
            if _overlaps(
                str(candidate["planned_departure"]),
                str(candidate["planned_arrival"]),
                str(assigned["planned_departure"]),
                str(assigned["planned_arrival"]),
            ):
                raise HTTPException(status_code=409, detail=f"{label} уже зайнятий у цей час.")


@router.get("/schedules", response_model=list[ScheduleResponse])
def list_schedules() -> list[ScheduleResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            """
            SELECT s.id, s.route_id, r.number AS route_number, r.name AS route_name,
                   s.departure_time, s.arrival_time, s.active
            FROM schedules s
            JOIN routes r ON r.id = s.route_id
            WHERE s.company_id = ?
            ORDER BY r.number COLLATE NOCASE, s.departure_time
            """,
            (company_id,),
        ).fetchall()
    return [_schedule_from_row(row) for row in rows]


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(payload: ScheduleInput) -> ScheduleResponse:
    departure = _validated_time(payload.departure_time, "виїзд")
    arrival = _validated_time(payload.arrival_time, "прибуття")
    if arrival <= departure:
        raise HTTPException(status_code=400, detail="Час прибуття має бути пізніше часу виїзду.")
    now = datetime.now(UTC).isoformat()
    schedule_id = str(uuid4())
    try:
        with _connection(write=True) as connection:
            company_id = _company_id(connection)
            route = connection.execute(
                "SELECT id FROM routes WHERE id = ? AND company_id = ? AND active = 1",
                (payload.route_id, company_id),
            ).fetchone()
            if route is None:
                raise HTTPException(status_code=400, detail="Маршрут недоступний.")
            connection.execute(
                """
                INSERT INTO schedules(
                    id, company_id, route_id, departure_time, arrival_time,
                    active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule_id,
                    company_id,
                    payload.route_id,
                    departure,
                    arrival,
                    int(payload.active),
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT s.id, s.route_id, r.number AS route_number, r.name AS route_name,
                       s.departure_time, s.arrival_time, s.active
                FROM schedules s JOIN routes r ON r.id = s.route_id
                WHERE s.id = ?
                """,
                (schedule_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Такий рейс уже є у розкладі маршруту.") from exc
    if row is None:
        raise HTTPException(status_code=500, detail="Розклад не створено.")
    return _schedule_from_row(row)


@router.post("/trips/generate", response_model=list[TripResponse])
def generate_trips(payload: TripGenerationInput) -> list[TripResponse]:
    service_date = payload.service_date.isoformat()
    now = datetime.now(UTC).isoformat()
    with _connection(write=True) as connection:
        company_id = _company_id(connection)
        schedules = connection.execute(
            """
            SELECT s.id, s.route_id, s.departure_time, s.arrival_time
            FROM schedules s
            JOIN routes r ON r.id = s.route_id
            WHERE s.company_id = ? AND s.active = 1 AND r.active = 1
            ORDER BY s.departure_time
            """,
            (company_id,),
        ).fetchall()
        for schedule in schedules:
            connection.execute(
                """
                INSERT OR IGNORE INTO trips(
                    id, company_id, schedule_id, route_id, service_date,
                    planned_departure, planned_arrival, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PLANNED', ?)
                """,
                (
                    str(uuid4()),
                    company_id,
                    str(schedule["id"]),
                    str(schedule["route_id"]),
                    service_date,
                    str(schedule["departure_time"]),
                    str(schedule["arrival_time"]),
                    now,
                ),
            )
        return _load_trips(connection, company_id, service_date)


@router.get("/trips", response_model=list[TripResponse])
def list_trips(service_date: date = Query(...)) -> list[TripResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        return _load_trips(connection, company_id, service_date.isoformat())


@router.get("/duties", response_model=list[DutyResponse])
def list_duties(service_date: date = Query(...)) -> list[DutyResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        ids = connection.execute(
            """
            SELECT id FROM duties
            WHERE company_id = ? AND service_date = ?
            ORDER BY duty_number COLLATE NOCASE
            """,
            (company_id, service_date.isoformat()),
        ).fetchall()
        return [_load_duty(connection, company_id, str(row["id"])) for row in ids]


@router.post("/duties", response_model=DutyResponse, status_code=201)
def create_duty(payload: DutyInput) -> DutyResponse:
    if len(set(payload.trip_ids)) != len(payload.trip_ids):
        raise HTTPException(status_code=400, detail="Один рейс не можна додати до наряду двічі.")

    service_date = payload.service_date.isoformat()
    duty_id = str(uuid4())
    placeholders = ",".join("?" for _ in payload.trip_ids)
    try:
        with _connection(write=True) as connection:
            company_id = _company_id(connection)
            vehicle = connection.execute(
                """
                SELECT id FROM vehicles
                WHERE id = ? AND company_id = ? AND lifecycle_status = 'ACTIVE'
                """,
                (payload.vehicle_id, company_id),
            ).fetchone()
            if vehicle is None:
                raise HTTPException(status_code=400, detail="Автобус недоступний для призначення.")

            driver = connection.execute(
                """
                SELECT id FROM drivers
                WHERE id = ? AND company_id = ? AND employment_status = 'ACTIVE'
                """,
                (payload.driver_id, company_id),
            ).fetchone()
            if driver is None:
                raise HTTPException(status_code=400, detail="Водій недоступний для призначення.")

            selected = connection.execute(
                f"""
                SELECT t.id, t.planned_departure, t.planned_arrival, t.status
                FROM trips t
                LEFT JOIN duty_trips dt ON dt.trip_id = t.id
                WHERE t.company_id = ? AND t.service_date = ?
                  AND t.id IN ({placeholders}) AND dt.trip_id IS NULL
                ORDER BY t.planned_departure
                """,
                (company_id, service_date, *payload.trip_ids),
            ).fetchall()
            if len(selected) != len(payload.trip_ids):
                raise HTTPException(
                    status_code=409,
                    detail="Один або кілька рейсів уже призначені або недоступні.",
                )
            if any(str(item["status"]) != "PLANNED" for item in selected):
                raise HTTPException(status_code=409, detail="До наряду можна додати лише заплановані рейси.")

            for previous, current in zip(selected, selected[1:], strict=False):
                if str(current["planned_departure"]) < str(previous["planned_arrival"]):
                    raise HTTPException(
                        status_code=409,
                        detail="Вибрані рейси перетинаються в часі.",
                    )

            _assert_resource_available(
                connection,
                company_id,
                service_date,
                "vehicle_id",
                payload.vehicle_id,
                selected,
                "Автобус",
            )
            _assert_resource_available(
                connection,
                company_id,
                service_date,
                "driver_id",
                payload.driver_id,
                selected,
                "Водій",
            )

            connection.execute(
                """
                INSERT INTO duties(
                    id, company_id, service_date, duty_number,
                    vehicle_id, driver_id, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'ASSIGNED', ?)
                """,
                (
                    duty_id,
                    company_id,
                    service_date,
                    payload.duty_number.strip(),
                    payload.vehicle_id,
                    payload.driver_id,
                    datetime.now(UTC).isoformat(),
                ),
            )
            connection.executemany(
                "INSERT INTO duty_trips(duty_id, trip_id, position) VALUES (?, ?, ?)",
                [
                    (duty_id, str(item["id"]), position)
                    for position, item in enumerate(selected, start=1)
                ],
            )
            connection.executemany(
                "UPDATE trips SET status = 'ASSIGNED' WHERE id = ?",
                [(str(item["id"]),) for item in selected],
            )
            return _load_duty(connection, company_id, duty_id)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Наряд з таким номером на цю дату вже існує.",
        ) from exc
