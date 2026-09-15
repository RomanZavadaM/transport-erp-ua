# Roadmap

## M0 — Architecture Freeze — COMPLETE
- domain model та state machines;
- PostgreSQL physical design/constraints;
- API/OpenAPI contract;
- permissions/RBAC;
- UX flows/workspaces;
- testing/traceability;
- i18n;
- deployment/backup/DR/observability;
- regulatory/business review.

Frozen baseline: `architecture-v1.5` після merge/tag final review.

## M1 — Foundation
- application skeleton;
- CI gates;
- consolidated OpenAPI;
- Alembic + migration #1;
- DB acceptance tests;
- Identity/RBAC/tenant isolation;
- audit/outbox/observability foundation.

## MVP implementation
- M2 Fleet & Drivers;
- M3 Routes/Schedules/Trips;
- M4 Duties/Dispatch;
- M5 Release/Checks;
- M6 Waybill/PDF/history;
- M7 Execution/Return/Close;
- M8 Reports + production hardening.

## Post-MVP
- GPS/live monitoring;
- mobile driver app;
- passenger accounting/ticketing;
- accounting/payroll;
- fuel-card integration;
- parts warehouse;
- external route-passport integration;
- advanced analytics/EDI.
