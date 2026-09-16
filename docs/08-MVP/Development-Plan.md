# План розробки MVP

## M0 — Architecture v1.5 — COMPLETE

Було зафіксовано domain model, API/OpenAPI, UX, permissions, testing, i18n, operations, regulatory review і traceability.

Перед M1.5 infrastructure baseline переглядається в **architecture-v1.6-local-first**, щоб продукт був практично придатний для малого АТП на одному комп’ютері.

## M1 — Foundation

### M1.1–M1.4 — DONE

- application skeleton;
- CI quality gates;
- consolidated OpenAPI;
- initial PostgreSQL migrations/invariants;
- Identity/RBAC/session security.

PostgreSQL work залишається основою Central profile, але Local Desktop переходить на SQLite.

### M1.5 — Local Desktop / SQLite / Transfer Foundation

Порядок:

1. SQLite local persistence profile;
2. local schema migrations;
3. application-data/documents directories;
4. local audit;
5. authority state;
6. prepare transfer batch;
7. mandatory local operator approval;
8. reliable delivery/retry;
9. Central idempotent receive + ACK;
10. local read-only enforcement після ACK;
11. backup/restore SQLite + documents;
12. lightweight local integrity/status screen;
13. desktop packaging/launcher spike;
14. acceptance tests на одному звичайному ПК.

M2 не стартує, поки не доведені сценарії:

- clean install без PostgreSQL/Docker;
- offline local operation;
- backup/restore;
- interrupted transfer;
- ACK → read-only;
- update/migration recovery.

## M2 — Fleet & Drivers

Автобуси, водії, документи, статуси та історія на local-first persistence foundation.

## M3 — Planning

Зупинки, маршрути, версії, розклад, генерація рейсів.

## M4 — Dispatch

Duty, призначення автобуса/водіїв, resource conflicts, Dispatcher workspace.

Local SQLite correctness перевіряється application transaction; Central PostgreSQL може мати додаткові exclusion constraints.

## M5 — Release

Передрейсові checks, compliance, authorization.

## M6 — Waybill

Нумерація, snapshots/versions, PDF, issue/return/close/correction.

Local file storage є baseline; server/S3 storage — optional Central profile.

## M7 — Execution & Closing

Фактичний рух, одометр, повернення, Trip/Duty close.

## M8 — Reports & Production Hardening

Local reports, Central consolidated reports, security, restore testing, performance та production readiness за реальним deployment profile.

## Принцип розвитку

Не додаємо server component, queue, cache, storage service або monitoring stack без конкретної задачі, яку він вирішує.
