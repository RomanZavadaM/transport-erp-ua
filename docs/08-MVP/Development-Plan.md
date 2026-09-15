# План розробки MVP

## M0 — Architecture Freeze — COMPLETE
Baseline: `architecture-v1.5` після merge/tag final review.

Зафіксовано domain model, PostgreSQL design, API/OpenAPI, UX, permissions, testing, i18n, production operations, regulatory review і traceability.

## M1 — Foundation
Порядок:
1. application skeleton;
2. CI quality gates;
3. consolidated OpenAPI validation;
4. Alembic bootstrap;
5. migration #1 + PostgreSQL acceptance tests;
6. Identity/RBAC/tenant isolation;
7. audit/outbox/observability foundation.

M2+ не стартують до проходження schema acceptance tests.

## M2 — Fleet & Drivers
Автобуси, водії, документи, статуси та історія.

## M3 — Planning
Зупинки, маршрути, версії, розклад, генерація рейсів.

## M4 — Dispatch
Duty, призначення автобуса/водіїв, resource conflicts, Dispatcher Board.

## M5 — Release
Передрейсові checks, compliance, authorization.

## M6 — Waybill
Нумерація, snapshots/versions, PDF, issue/return/close/correction.

## M7 — Execution & Closing
Фактичний рух, одометр, повернення, Trip/Duty close.

## M8 — Reports & Production Hardening
Operational reports, security, concurrency, restore testing, performance, production readiness.
