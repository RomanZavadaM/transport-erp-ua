# TransportERP-UA

Web-based transport enterprise management system for Ukraine.

The system is intended to automate transport operations, including fleet and driver registries, routes and schedules, trip planning, operational duties, pre-trip medical and technical control, dispatcher release authorization, waybills, actual movement, mileage, fuel, maintenance, repairs, documents, reporting, users, roles, and audit.

## Architecture baseline

Current architecture baseline: **v1.3**.

Core decisions:

- modular monolith for the first production versions;
- PostgreSQL as the transactional source of truth;
- `Trip != Duty`: a duty is an operational vehicle/crew shift and may contain one or more trips;
- release belongs to a duty;
- a waybill is based on a duty and may cover 1..N trips;
- plan and fact are stored separately;
- closed operational history and document versions are immutable;
- corrections create new versions/snapshots instead of silently rewriting history;
- command-oriented REST API for critical state changes;
- append-only audit and operational event history;
- PostgreSQL exclusion constraints protect against overlapping vehicle and driver assignments;
- optimistic locking and idempotency protect concurrent dispatcher operations;
- outbox events prepare the core for future integrations;
- tenant/company isolation is enforced throughout the data model.

## Documentation

The `/docs` directory is designed to be opened directly as an **Obsidian Vault** while remaining ordinary Markdown readable in GitHub and code editors.

Start at:

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — current project checkpoint;
- [`ARCHITECTURE_VERSION.md`](ARCHITECTURE_VERSION.md) — architecture baseline;
- [`docs/_index.md`](docs/_index.md) — documentation index;
- [`docs/01-Architecture/ADR`](docs/01-Architecture/ADR) — architecture decision records;
- [`docs/01-Architecture/Business-Rules`](docs/01-Architecture/Business-Rules) — numbered business rules;
- [`docs/11-Traceability`](docs/11-Traceability) — requirement → rule → API → DB → test traceability.

## Planned source layout

```text
backend/     FastAPI application
frontend/    React / Next.js application
infra/       deployment and infrastructure
docs/        architecture / product documentation and Obsidian Vault
templates/   documentation templates
```

The application source directories will be introduced only after the MVP architecture and contracts are frozen.