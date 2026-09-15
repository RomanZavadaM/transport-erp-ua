# TransportERP-UA — English

Translation status: `current`  
Canonical source: [`README.md`](../../../README.md)

**The canonical language of the project is Ukrainian.** If this translation differs from the Ukrainian source, the Ukrainian text prevails.

TransportERP-UA is a web system for a Ukrainian transport enterprise. It is intended to support fleet and driver registries, routes and schedules, trip planning, operational duties, release to line, pre-trip controls, waybills, actual movement, mileage, fuel, maintenance and repairs, documents, reporting, roles and audit.

## Architecture baseline

Current baseline: **v1.3**.

Key decisions:

- modular monolith for the first production versions;
- PostgreSQL as the transactional source of truth;
- `Trip` and `Duty` are separate domain concepts;
- one Duty may contain multiple Trips;
- Release belongs to Duty;
- Waybill is based on Duty and may cover multiple Trips;
- plan and actual data are separated;
- closed history and document versions are immutable;
- corrections create new versions instead of rewriting history;
- critical state changes use explicit business commands;
- audit and operational events are append-only;
- PostgreSQL constraints protect resource allocation under concurrency.

The full canonical documentation is maintained in Ukrainian under [`/docs`](../../).
