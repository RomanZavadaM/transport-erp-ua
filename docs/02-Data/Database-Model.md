# Database Model

PostgreSQL is the transactional source of truth.

Core tables include:

- companies, depots, users, roles, permissions;
- vehicles and vehicle_documents;
- drivers and driver_documents;
- stops, routes, route_versions, route_stops;
- schedules, schedule_versions, schedule_runs;
- trips, trip_stop_plan, trip_actuals, trip_actual_snapshots, trip_events;
- duties, duty_trips, resource assignments and actual usage;
- releases, pre_trip_checks, compliance evaluations and authorizations;
- waybills, waybill_versions, waybill_trips, number_sequences;
- files and attachments;
- fuel operations;
- defects, maintenance and repair orders;
- correction_cases;
- audit_log, outbox_events and integrity alerts.

Primary identifiers use UUIDs. Instants use `timestamptz`. Operational data is normalized; historical document/fact representations are immutable snapshots.
