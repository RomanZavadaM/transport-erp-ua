# PROJECT_STATE

## Поточний baseline

Архітектура: **architecture-v1.5**  
Статус архітектури: **M0 Architecture Freeze — FROZEN**  
Канонічна мова: **українська (`uk`)**; переклади: `en`, `es`, `fr`, `de`.

Поточний етап реалізації: **M1.4 — Identity and access foundation**.

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

## M0 завершено

- MVP Definition Package;
- API Contract Package `/api/v1`;
- PostgreSQL Physical Schema v1 — 77 core tables;
- UX/wireframes/workspaces;
- RBAC/permissions/separation of duties;
- i18n contract `uk/en/es/fr/de`;
- testing/acceptance/traceability;
- production topology, backup/PITR, DR, observability;
- regulatory/business review `MR-001..MR-007`.

## M1 — стан реалізації

### M1.1 Application skeleton + CI — DONE

- FastAPI backend skeleton;
- Next.js + TypeScript frontend skeleton;
- development Docker Compose;
- CI gates: Ruff, strict mypy, pytest, ESLint, TypeScript, production build, Compose validation.

Merged to `main` as commit `f85c6b9…`.

### M1.2 Consolidated OpenAPI — DONE

- base OpenAPI + freeze overlay;
- deterministic consolidator;
- machine-readable canonical `docs/03-API/openapi-mvp-v1-consolidated.yaml`;
- structural OpenAPI 3.1 validation;
- freeze-invariant validation;
- CI drift check.

Merged to `main` as commit `27ac384…`.

### M1.3 Alembic migration #1 + PostgreSQL invariants — DONE

Merged to `main` as commit:

`d64c765b9ed6ee7acdf1add12fbf4ae26edeeba8`

Implemented:

- Alembic bootstrap;
- PostgreSQL 16 physical schema;
- all **77 core tables**;
- `pgcrypto`, `citext`, `btree_gist`;
- tenant-aware FK;
- RLS;
- immutable history triggers;
- GiST `EXCLUDE` constraints for vehicle/driver time conflicts;
- route/schedule version overlap protection;
- generated Trip uniqueness;
- PRIMARY Waybill constraint;
- medical result set `FIT | UNFIT`;
- separate `DRIVER_TECHNICAL_PREDEPARTURE` check type;
- full initial downgrade.

CI lifecycle verified:

`upgrade head → 12 PostgreSQL acceptance tests → downgrade base → upgrade head → schema verification`

Acceptance suite verifies, among other things:

- exactly 77 core tables;
- cross-tenant FK rejection;
- vehicle double-booking rejection;
- driver double-booking rejection;
- duplicate generated Trip rejection;
- second active PRIMARY Waybill rejection;
- invalid medical result rejection;
- append-only/immutable historical records;
- RLS tenant isolation.

Issue #18 is closed.

## M1.4 — Identity and access foundation — ACTIVE

GitHub Issue: **#19**.

Goal: implement the base users/roles/permissions/session/tenant access layer on top of the already-created PostgreSQL identity schema.

Already confirmed before implementation:

- backend authorizes by **permission code**, not hardcoded role name;
- tenant isolation is independent from RBAC;
- administrator permissions do not implicitly grant dispatcher/medical/technical business permissions;
- role permissions must support separation-of-duties policy;
- `users`, `user_sessions`, `roles`, `permissions`, `user_roles`, `role_permissions` already exist in migration #1;
- browser auth must avoid long-lived credentials in localStorage;
- canonical permission catalog: `docs/03-API/Permissions-Catalog.md`;
- canonical identity schema: `docs/02-Data/schema/01-Organization-Identity.md`.

### Planned M1.4 implementation order

1. create `identity` backend module boundaries (`domain/application/infrastructure/api`);
2. database transaction/session abstraction with tenant context (`SET LOCAL app.company_id`);
3. password hashing with Argon2id;
4. user repository and status handling (`ACTIVE/SUSPENDED/DISABLED`);
5. role/permission repositories and effective-permission resolution;
6. session issuance using opaque random token + only token hash stored in DB;
7. secure session cookie contract and logout/revocation;
8. `/api/v1/auth/login`, `/logout`, `/me`, `/permissions`;
9. reusable FastAPI `require_permission(...)` dependency;
10. user/role management foundation required by MVP;
11. PostgreSQL integration tests for tenant/RBAC/session isolation;
12. API tests for 401/403, suspended/disabled users, revoked/expired sessions and permission enforcement;
13. CI green before merge.

M1.4 is **not yet implemented** at this checkpoint; analysis of Issue #19, permissions catalog and identity schema has started.

## Next after M1.4

M1.5 — audit/outbox/observability foundation (Issue #20).

Only after M1 foundation is complete do we move to M2 Fleet & Drivers business modules.

## Regulatory baseline

State verified on 15.09.2026. Canonical documents:

- `docs/10-Legal/Regulatory-Register.md`;
- `docs/10-Legal/Regulatory-Review-2026-09.md`;
- `docs/10-Legal/MR-Decision-Register.md`;
- `docs/10-Legal/Regulatory-Change-Log.md`.

Traceability: `source → MR decision → BR-* → API/DB/policy → AT-*`.

## Deferred — not blockers for M1

- GPS/live monitoring;
- passenger accounting/e-ticketing;
- mobile driver app;
- payroll/accounting;
- fuel-card integration;
- parts warehouse;
- external route-passport integration;
- advanced analytics;
- additional non-primary document roles;
- final enterprise retention periods.

Deferred work cannot change frozen M0 invariants without ADR + impact review.

## Repository governance

- `docs/` — canonical Obsidian Vault;
- significant changes — branch + Pull Request;
- accepted ADR are not silently rewritten;
- Business Rule IDs: `BR-*`;
- Acceptance Test IDs: `AT-*`;
- secrets and production data are never stored in Git.
