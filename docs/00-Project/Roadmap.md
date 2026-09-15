# Roadmap

## M0 — Architecture v1.5 — COMPLETE

Зафіксовано domain model/state machines, API/OpenAPI, permissions/RBAC, UX, testing/traceability, i18n, regulatory review та початковий server-oriented physical design.

## Architecture v1.6 — Local-first review — ACTIVE

Перед M1.5 переглянуто надлишкову infrastructure complexity.

Цільові рішення:

- local рівень = встановлюваний desktop application;
- local operational DB = SQLite;
- local documents = managed filesystem;
- робота без Internet/central;
- PostgreSQL = optional Central profile;
- передача даних тільки після local operator approval;
- central ACK → local read-only;
- backup/restore через сам застосунок;
- Redis/S3/Docker/Kubernetes не є local prerequisites.

## M1 — Foundation

### DONE
- application skeleton;
- CI gates;
- OpenAPI;
- initial PostgreSQL/server migration foundation;
- Identity/RBAC/session security.

### M1.5 — NEXT
- SQLite local persistence;
- local migrations;
- desktop application-data layout;
- audit;
- transfer approval + reliable delivery;
- central idempotent receive + ACK;
- local read-only enforcement;
- backup/restore;
- lightweight system status/integrity;
- desktop packaging spike.

## MVP implementation

- M2 Fleet & Drivers;
- M3 Routes/Schedules/Trips;
- M4 Duties/Dispatch;
- M5 Release/Checks;
- M6 Waybill/PDF/history;
- M7 Execution/Return/Close;
- M8 Reports + production hardening.

Усі M2+ модулі спочатку мають працювати на Local SQLite. Central PostgreSQL додає консолідацію/вищий рівень без зміни локальної бізнес-логіки.

## Post-MVP

- GPS/live monitoring;
- mobile driver app;
- passenger accounting/ticketing;
- accounting/payroll;
- fuel-card integration;
- parts warehouse;
- external route-passport integration;
- advanced analytics/EDI.
