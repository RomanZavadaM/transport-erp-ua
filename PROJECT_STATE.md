# PROJECT_STATE

## Поточний baseline

Версія: **architecture-v1.5**  
Статус: **M0 Architecture Freeze — FROZEN**  
Канонічна мова: **українська (`uk`)**; підтримувані переклади: `en`, `es`, `fr`, `de`.

## Frozen core decisions

- Modular Monolith.
- PostgreSQL — транзакційне джерело істини.
- `Trip != Duty`; Duty містить 1..N Trips.
- `Release` належить Duty.
- Waybill — versioned enterprise document, пов'язаний з Duty і 1..N Trips.
- Plan і Fact розділені.
- CLOSED history immutable; correction створює новий snapshot/version.
- Audit та operational events append-only.
- PostgreSQL `EXCLUDE/UNIQUE/FK/CHECK` захищають critical invariants.
- Optimistic locking + ETag/If-Match захищають від lost update.
- Critical commands використовують idempotency.
- Tenant isolation + RLS — частина physical design.
- Transactional outbox та integrity checker закладені в core.

## M0 packages завершено

- MVP Definition Package;
- API Contract Package `/api/v1`;
- PostgreSQL Physical Schema v1 — 77 core tables;
- UX/wireframes/workspaces;
- RBAC/permissions/separation of duties;
- i18n contract `uk/en/es/fr/de`;
- testing/acceptance/traceability;
- production topology, backup/PITR, DR, observability;
- regulatory/business review `MR-001..MR-007`.

## Final cross-document corrections

Physical schema/API синхронізовані з review:

- medical result set: `FIT | UNFIT`;
- separate `DRIVER_TECHNICAL_PREDEPARTURE` evidence;
- technical checker — qualification/permission based actor;
- multi-driver crew model + `crew_mode`;
- context/version-aware document compliance;
- Waybill explicit `document_role`;
- M0 default: один active `PRIMARY` Waybill на Duty;
- class-based file retention metadata;
- OpenAPI freeze overlay виправляє застарілі деталі base draft.

Machine API contract M1:

- `docs/03-API/openapi-mvp-v1.yaml`;
- `docs/03-API/openapi-mvp-v1-freeze-overlay.yaml`.

Перед backend implementation вони мають бути зведені у consolidated OpenAPI та пройти validation/contract tests.

## Regulatory baseline

Стан перевірено на 15.09.2026. Канонічні документи:

- `docs/10-Legal/Regulatory-Register.md`;
- `docs/10-Legal/Regulatory-Review-2026-09.md`;
- `docs/10-Legal/MR-Decision-Register.md`;
- `docs/10-Legal/Regulatory-Change-Log.md`.

Traceability: `source → MR decision → BR-* → API/DB/policy → AT-*`.

## Deferred — не blockers для M1

- GPS / live monitoring;
- passenger accounting / e-ticketing;
- mobile driver app;
- payroll/accounting;
- fuel-card integration;
- parts warehouse;
- external route-passport integration;
- advanced analytics;
- additional non-primary document roles;
- final enterprise retention periods.

Deferred work не може змінювати frozen M0 invariants без ADR + impact review.

## M1 — наступний milestone

Після merge цього freeze baseline і створення tag `architecture-v1.5` порядок старту:

1. application repository skeleton;
2. CI quality gates;
3. consolidated OpenAPI validation;
4. Alembic bootstrap;
5. migration #1 + PostgreSQL acceptance tests;
6. identity/RBAC/tenant foundation;
7. audit/outbox/observability foundation.

До проходження schema acceptance tests модулі M2+ не вважаються готовими до реалізації.

## Repository governance

- `docs/` — канонічний Obsidian Vault;
- значні зміни — branch + Pull Request;
- accepted ADR не переписуються із приховуванням історії;
- Business Rule IDs: `BR-*`;
- Acceptance Test IDs: `AT-*`;
- secrets та production data у Git не зберігаються.
