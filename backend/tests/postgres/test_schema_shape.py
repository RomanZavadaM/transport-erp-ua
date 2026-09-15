from __future__ import annotations

import pytest
from psycopg import Connection

pytestmark = pytest.mark.postgres

CORE_TABLES = {
    "companies",
    "company_settings",
    "depots",
    "users",
    "user_sessions",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "api_idempotency_keys",
    "vehicle_types",
    "fuel_types",
    "vehicles",
    "vehicle_status_history",
    "vehicle_runtime_state",
    "vehicle_document_types",
    "vehicle_documents",
    "vehicle_odometer_readings",
    "drivers",
    "driver_status_history",
    "driver_document_types",
    "driver_documents",
    "stops",
    "routes",
    "route_versions",
    "route_stops",
    "schedules",
    "schedule_versions",
    "service_calendars",
    "service_calendar_exceptions",
    "schedule_runs",
    "schedule_stop_times",
    "trips",
    "trip_stop_plan",
    "trip_actuals",
    "trip_stop_actuals",
    "trip_actual_snapshots",
    "trip_events",
    "duties",
    "duty_trips",
    "duty_vehicle_assignments",
    "duty_driver_assignments",
    "duty_vehicle_usage",
    "duty_driver_usage",
    "duty_events",
    "releases",
    "check_templates",
    "check_template_items",
    "pre_trip_checks",
    "medical_check_details",
    "technical_check_details",
    "check_results",
    "pre_trip_check_invalidations",
    "compliance_rules",
    "release_rule_evaluations",
    "release_authorizations",
    "number_sequences",
    "document_templates",
    "document_template_versions",
    "waybills",
    "waybill_trips",
    "waybill_versions",
    "files",
    "entity_attachments",
    "fuel_operations",
    "defects",
    "maintenance_types",
    "maintenance_plans",
    "maintenance_events",
    "repair_orders",
    "repair_order_items",
    "correction_cases",
    "audit_log",
    "audit_partition_seals",
    "outbox_events",
    "report_exports",
    "system_integrity_alerts",
}


def test_exact_core_table_catalog(pg: Connection[tuple[object, ...]]) -> None:
    rows = pg.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND table_name <> 'alembic_version'
        """
    ).fetchall()
    actual = {str(row[0]) for row in rows}

    assert len(CORE_TABLES) == 77
    assert actual == CORE_TABLES


def test_required_extensions(pg: Connection[tuple[object, ...]]) -> None:
    rows = pg.execute(
        "SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto','citext','btree_gist')"
    ).fetchall()
    assert {str(row[0]) for row in rows} == {"pgcrypto", "citext", "btree_gist"}


def test_rls_enabled_on_core_tenant_tables(pg: Connection[tuple[object, ...]]) -> None:
    rows = pg.execute(
        """
        SELECT relname, relrowsecurity
        FROM pg_class
        WHERE relnamespace = 'public'::regnamespace
          AND relname IN ('companies','vehicles','drivers','trips','duties','releases','waybills')
        """
    ).fetchall()

    assert rows
    assert all(bool(row[1]) for row in rows)
