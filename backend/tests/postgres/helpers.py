from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg import Connection


def create_company(pg: Connection[Any], *, name: str = "Test Company") -> UUID:
    company_id = uuid4()
    edrpou = f"{company_id.int % 100_000_000:08d}"
    pg.execute(
        """
        INSERT INTO companies (id, name, legal_name, edrpou)
        VALUES (%s, %s, %s, %s)
        """,
        (company_id, name, name, edrpou),
    )
    return company_id


def create_user(pg: Connection[Any], company_id: UUID) -> UUID:
    user_id = uuid4()
    pg.execute(
        """
        INSERT INTO users (id, company_id, username, password_hash)
        VALUES (%s, %s, %s, 'test-hash')
        """,
        (user_id, company_id, f"user-{user_id}"),
    )
    return user_id


def create_depot(pg: Connection[Any], company_id: UUID) -> UUID:
    depot_id = uuid4()
    pg.execute(
        "INSERT INTO depots (id, company_id, code, name) VALUES (%s, %s, %s, 'Depot')",
        (depot_id, company_id, f"D-{str(depot_id)[:8]}"),
    )
    return depot_id


def create_vehicle(pg: Connection[Any], company_id: UUID) -> UUID:
    vehicle_id = uuid4()
    token = str(vehicle_id).replace("-", "")[:10].upper()
    pg.execute(
        """
        INSERT INTO vehicles (
            id, company_id, fleet_number, registration_number, make, model
        ) VALUES (%s, %s, %s, %s, 'Test', 'Bus')
        """,
        (vehicle_id, company_id, f"F-{token}", f"REG-{token}"),
    )
    return vehicle_id


def create_driver(pg: Connection[Any], company_id: UUID) -> UUID:
    driver_id = uuid4()
    pg.execute(
        """
        INSERT INTO drivers (
            id, company_id, personnel_number, last_name, first_name
        ) VALUES (%s, %s, %s, 'Тестовий', 'Водій')
        """,
        (driver_id, company_id, f"P-{str(driver_id)[:12]}"),
    )
    return driver_id


def create_duty(pg: Connection[Any], company_id: UUID, suffix: str | None = None) -> UUID:
    duty_id = uuid4()
    duty_number = suffix or str(duty_id)[:12]
    pg.execute(
        """
        INSERT INTO duties (
            id, company_id, service_date, duty_number,
            planned_start_at, planned_end_at
        ) VALUES (
            %s, %s, DATE '2026-09-15', %s,
            TIMESTAMPTZ '2026-09-15 08:00:00+03',
            TIMESTAMPTZ '2026-09-15 18:00:00+03'
        )
        """,
        (duty_id, company_id, f"DUTY-{duty_number}"),
    )
    return duty_id


def create_route_version(pg: Connection[Any], company_id: UUID) -> UUID:
    route_id = uuid4()
    route_version_id = uuid4()
    pg.execute(
        """
        INSERT INTO routes (id, company_id, route_number, name, route_type)
        VALUES (%s, %s, %s, 'Test route', 'REGULAR')
        """,
        (route_id, company_id, f"R-{str(route_id)[:8]}"),
    )
    pg.execute(
        """
        INSERT INTO route_versions (
            id, company_id, route_id, version_no, valid_period, status
        ) VALUES (%s, %s, %s, 1, daterange('2026-01-01','2027-01-01','[)'), 'ACTIVE')
        """,
        (route_version_id, company_id, route_id),
    )
    return route_version_id


def create_schedule_run(
    pg: Connection[Any], company_id: UUID, route_version_id: UUID
) -> UUID:
    route_id = pg.execute(
        "SELECT route_id FROM route_versions WHERE id = %s",
        (route_version_id,),
    ).fetchone()[0]
    schedule_id = uuid4()
    schedule_version_id = uuid4()
    calendar_id = uuid4()
    run_id = uuid4()

    pg.execute(
        """
        INSERT INTO schedules (id, company_id, route_id, code, name, status)
        VALUES (%s, %s, %s, %s, 'Test schedule', 'ACTIVE')
        """,
        (schedule_id, company_id, route_id, f"SCH-{str(schedule_id)[:8]}"),
    )
    pg.execute(
        """
        INSERT INTO schedule_versions (
            id, company_id, schedule_id, version_no, route_version_id, valid_period, status
        ) VALUES (
            %s, %s, %s, 1, %s, daterange('2026-01-01','2027-01-01','[)'), 'ACTIVE'
        )
        """,
        (schedule_version_id, company_id, schedule_id, route_version_id),
    )
    pg.execute(
        """
        INSERT INTO service_calendars (
            id, company_id, name, monday, tuesday, wednesday,
            thursday, friday, saturday, sunday, valid_period
        ) VALUES (
            %s, %s, 'Daily', true, true, true, true, true, true, true,
            daterange('2026-01-01','2027-01-01','[)')
        )
        """,
        (calendar_id, company_id),
    )
    pg.execute(
        """
        INSERT INTO schedule_runs (
            id, company_id, schedule_version_id, service_calendar_id,
            run_code, direction, departure_time, arrival_time
        ) VALUES (%s, %s, %s, %s, %s, 0, TIME '09:00', TIME '10:00')
        """,
        (run_id, company_id, schedule_version_id, calendar_id, f"RUN-{str(run_id)[:8]}"),
    )
    return run_id


def create_trip(
    pg: Connection[Any],
    company_id: UUID,
    route_version_id: UUID,
    *,
    schedule_run_id: UUID | None = None,
) -> UUID:
    trip_id = uuid4()
    pg.execute(
        """
        INSERT INTO trips (
            id, company_id, service_date, schedule_run_id, route_version_id,
            planned_departure_at, planned_arrival_at
        ) VALUES (
            %s, %s, DATE '2026-09-15', %s, %s,
            TIMESTAMPTZ '2026-09-15 09:00:00+03',
            TIMESTAMPTZ '2026-09-15 10:00:00+03'
        )
        """,
        (trip_id, company_id, schedule_run_id, route_version_id),
    )
    return trip_id
