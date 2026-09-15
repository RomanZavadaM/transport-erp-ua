from __future__ import annotations

from typing import Any
from uuid import uuid4

import psycopg
from psycopg import Connection, errors

from .helpers import (
    create_company,
    create_depot,
    create_driver,
    create_duty,
    create_route_version,
    create_schedule_run,
    create_trip,
    create_user,
    create_vehicle,
)


def test_cross_tenant_depot_fk_is_rejected(pg: Connection[Any]) -> None:
    company_a = create_company(pg, name="Tenant A")
    company_b = create_company(pg, name="Tenant B")
    depot_a = create_depot(pg, company_a)
    vehicle_id = uuid4()
    token = str(vehicle_id).replace("-", "")[:10].upper()

    try:
        with pg.transaction():
            pg.execute(
                """
                INSERT INTO vehicles (
                    id, company_id, depot_id, fleet_number, registration_number, make, model
                ) VALUES (%s, %s, %s, %s, %s, 'Test', 'Bus')
                """,
                (vehicle_id, company_b, depot_a, f"F-{token}", f"REG-{token}"),
            )
    except errors.ForeignKeyViolation:
        return
    raise AssertionError("cross-tenant depot reference was accepted")


def test_vehicle_assignment_overlap_is_rejected(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    vehicle_id = create_vehicle(pg, company_id)
    duty_a = create_duty(pg, company_id, "A")
    duty_b = create_duty(pg, company_id, "B")

    pg.execute(
        """
        INSERT INTO duty_vehicle_assignments (
            company_id, duty_id, vehicle_id, assignment_period
        ) VALUES (
            %s, %s, %s,
            tstzrange('2026-09-15 08:00:00+03','2026-09-15 12:00:00+03','[)')
        )
        """,
        (company_id, duty_a, vehicle_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                """
                INSERT INTO duty_vehicle_assignments (
                    company_id, duty_id, vehicle_id, assignment_period
                ) VALUES (
                    %s, %s, %s,
                    tstzrange('2026-09-15 11:00:00+03','2026-09-15 15:00:00+03','[)')
                )
                """,
                (company_id, duty_b, vehicle_id),
            )
    except errors.ExclusionViolation:
        return
    raise AssertionError("overlapping vehicle assignment was accepted")


def test_driver_assignment_overlap_is_rejected(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    driver_id = create_driver(pg, company_id)
    duty_a = create_duty(pg, company_id, "DA")
    duty_b = create_duty(pg, company_id, "DB")

    pg.execute(
        """
        INSERT INTO duty_driver_assignments (
            company_id, duty_id, driver_id, assignment_role, assignment_period
        ) VALUES (
            %s, %s, %s, 'PRIMARY',
            tstzrange('2026-09-15 08:00:00+03','2026-09-15 12:00:00+03','[)')
        )
        """,
        (company_id, duty_a, driver_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                """
                INSERT INTO duty_driver_assignments (
                    company_id, duty_id, driver_id, assignment_role, assignment_period
                ) VALUES (
                    %s, %s, %s, 'RELIEF',
                    tstzrange('2026-09-15 11:59:00+03','2026-09-15 16:00:00+03','[)')
                )
                """,
                (company_id, duty_b, driver_id),
            )
    except errors.ExclusionViolation:
        return
    raise AssertionError("overlapping driver assignment was accepted")


def test_generated_trip_is_unique_per_run_and_service_date(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    route_version_id = create_route_version(pg, company_id)
    schedule_run_id = create_schedule_run(pg, company_id, route_version_id)
    create_trip(
        pg,
        company_id,
        route_version_id,
        schedule_run_id=schedule_run_id,
    )

    try:
        with pg.transaction():
            create_trip(
                pg,
                company_id,
                route_version_id,
                schedule_run_id=schedule_run_id,
            )
    except errors.UniqueViolation:
        return
    raise AssertionError("duplicate generated trip was accepted")


def test_only_one_non_cancelled_primary_waybill_per_duty(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    duty_id = create_duty(pg, company_id)
    pg.execute(
        """
        INSERT INTO waybills (company_id, duty_id, series, number, full_number)
        VALUES (%s, %s, 'A', 1, 'A-1')
        """,
        (company_id, duty_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                """
                INSERT INTO waybills (company_id, duty_id, series, number, full_number)
                VALUES (%s, %s, 'A', 2, 'A-2')
                """,
                (company_id, duty_id),
            )
    except errors.UniqueViolation:
        return
    raise AssertionError("second active PRIMARY waybill was accepted")


def test_medical_result_is_strict_fit_or_unfit(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    actor_id = create_user(pg, company_id)
    driver_id = create_driver(pg, company_id)
    duty_id = create_duty(pg, company_id)
    release_id = uuid4()
    check_id = uuid4()

    pg.execute(
        "INSERT INTO releases (id, company_id, duty_id) VALUES (%s, %s, %s)",
        (release_id, company_id, duty_id),
    )
    pg.execute(
        """
        INSERT INTO pre_trip_checks (
            id, company_id, release_id, check_type, subject_type, subject_id,
            status, completed_at, performed_by
        ) VALUES (
            %s, %s, %s, 'MEDICAL', 'DRIVER', %s,
            'PASSED', now(), %s
        )
        """,
        (check_id, company_id, release_id, driver_id, actor_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                """
                INSERT INTO medical_check_details (
                    pre_trip_check_id, company_id, driver_id, fitness_result
                ) VALUES (%s, %s, %s, 'UNKNOWN')
                """,
                (check_id, company_id, driver_id),
            )
    except errors.CheckViolation:
        return
    raise AssertionError("unsupported medical result was accepted")


def test_append_only_duty_event_cannot_be_updated(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    duty_id = create_duty(pg, company_id)
    event_id = uuid4()
    pg.execute(
        """
        INSERT INTO duty_events (id, company_id, duty_id, event_type, occurred_at, source)
        VALUES (%s, %s, %s, 'CREATED', now(), 'TEST')
        """,
        (event_id, company_id, duty_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                "UPDATE duty_events SET event_type = 'MUTATED' WHERE id = %s",
                (event_id,),
            )
    except psycopg.Error as exc:
        assert exc.sqlstate == "55000"
        return
    raise AssertionError("append-only duty event was updated")


def test_completed_pre_trip_check_cannot_be_rewritten(pg: Connection[Any]) -> None:
    company_id = create_company(pg)
    actor_id = create_user(pg, company_id)
    driver_id = create_driver(pg, company_id)
    duty_id = create_duty(pg, company_id)
    release_id = uuid4()
    check_id = uuid4()
    pg.execute(
        "INSERT INTO releases (id, company_id, duty_id) VALUES (%s, %s, %s)",
        (release_id, company_id, duty_id),
    )
    pg.execute(
        """
        INSERT INTO pre_trip_checks (
            id, company_id, release_id, check_type, subject_type, subject_id,
            status, completed_at, performed_by
        ) VALUES (
            %s, %s, %s, 'MEDICAL', 'DRIVER', %s,
            'PASSED', now(), %s
        )
        """,
        (check_id, company_id, release_id, driver_id, actor_id),
    )

    try:
        with pg.transaction():
            pg.execute(
                "UPDATE pre_trip_checks SET status = 'FAILED' WHERE id = %s",
                (check_id,),
            )
    except psycopg.Error as exc:
        assert exc.sqlstate == "55000"
        return
    raise AssertionError("completed pre-trip check was rewritten")


def test_rls_isolates_tenants_for_runtime_role(pg: Connection[Any]) -> None:
    company_a = create_company(pg, name="RLS A")
    company_b = create_company(pg, name="RLS B")
    create_vehicle(pg, company_a)
    create_vehicle(pg, company_b)
    role_name = f"rls_test_{uuid4().hex[:12]}"

    pg.execute(f'CREATE ROLE "{role_name}" NOLOGIN')
    try:
        pg.execute(f'GRANT USAGE ON SCHEMA public TO "{role_name}"')
        pg.execute(f'GRANT SELECT ON companies, vehicles TO "{role_name}"')
        pg.execute(f'SET ROLE "{role_name}"')
        pg.execute("SELECT set_config('app.company_id', %s, false)", (str(company_a),))

        company_ids = {row[0] for row in pg.execute("SELECT id FROM companies").fetchall()}
        vehicle_companies = {
            row[0] for row in pg.execute("SELECT company_id FROM vehicles").fetchall()
        }
        assert company_ids == {company_a}
        assert vehicle_companies == {company_a}
    finally:
        pg.execute("RESET ROLE")
        pg.execute(f'DROP OWNED BY "{role_name}"')
        pg.execute(f'DROP ROLE IF EXISTS "{role_name}"')
