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

MVP, API contract, PostgreSQL physical design, UX, RBAC policy, i18n, testing/traceability, operations/DR та regulatory review завершені й frozen у architecture-v1.5.

## M1 — стан реалізації

### M1.1 Application skeleton + CI — DONE

Merged to `main` as `f85c6b9…`.

### M1.2 Consolidated OpenAPI — DONE

Merged to `main` as `27ac384…`.

### M1.3 Alembic migration #1 + PostgreSQL invariants — DONE

Merged to `main` as:

`d64c765b9ed6ee7acdf1add12fbf4ae26edeeba8`

CI lifecycle verified:

`upgrade head → 12 PostgreSQL acceptance tests → downgrade base → upgrade head → schema verification`

Issue #18 closed.

## M1.4 — Identity and access foundation — ACTIVE, IMPLEMENTED IN PR

GitHub Issue: **#19**  
Working branch: **`feature/m1.4-identity-access`**  
Draft PR: **#24**.

### Durable implementation checkpoints

- `e627bb886521cffd2b2aee9323d0e4a71fc29a85` — identity domain/application/persistence foundation + migration #2;
- `2e8a0f75f928023adf4c8da058956e9eac2dd9d6` — cookie session auth, RBAC HTTP API, CSRF middleware;
- `0f8add2285f1d594c2b666b03c430e8d97dd42ce` — identity security and PostgreSQL acceptance tests;
- `90729275c3dbdf64d99c699633d4cd3dfc0779e0` — CI diagnostics fixes + safe client IP normalization;
- `fadfd0e0f592dea3026ab0a4b636a7400f2305c1` — strict mypy test fix;
- `8d98514da20622dc3b9884054971e9de95d97373` — OpenAPI overlay synchronized with identity/session API;
- `12213baa2e2c4c7e7582142e3e95683bdc531b2b` — CI-generated consolidated OpenAPI contract.

### Implemented in M1.4

- bounded context `identity/domain/application/infrastructure/api`;
- SQLAlchemy session factory and transaction-local tenant context via `SET LOCAL app.company_id`;
- Argon2id password hashing;
- opaque cryptographically-random session tokens;
- only SHA-256 session-token hash stored in PostgreSQL;
- HttpOnly browser session cookie;
- double-submit CSRF protection bound to current session;
- production guard requiring secure cookies;
- session login/rotation/revocation;
- user status handling `ACTIVE/SUSPENDED/DISABLED`;
- permission-based authorization, not hardcoded role names;
- effective permission resolution;
- users/roles/permissions management foundation;
- reusable FastAPI `require_permission(...)` dependency;
- request-id and stable API error envelope;
- `/api/v1/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`, `/auth/permissions`;
- `/api/v1/users` create/list/get/patch/status/roles foundation;
- `/api/v1/roles` and `/api/v1/permissions` foundation;
- migration #2 with complete frozen permission catalog seed;
- system `ADMIN` template role with identity/settings/audit permissions only;
- ADMIN does **not** implicitly receive release/medical/technical permissions;
- narrow PostgreSQL `SECURITY DEFINER` company bootstrap resolver for login;
- DB trigger rejecting cross-tenant role assignment;
- identity unit tests and real PostgreSQL/API acceptance tests;
- OpenAPI overlay now describes cookie auth, CSRF, users/roles endpoints and identity DTOs.

### CI findings already resolved

- Ruff import/encoding diagnostics resolved without weakening Ruff rules;
- TestClient peer name `testclient` is not forced into PostgreSQL `inet`; application stores peer IP only when syntactically valid;
- strict mypy complaint over psycopg `object` result fixed with explicit typed cast;
- migration #2 already succeeded on clean PostgreSQL in CI;
- OpenAPI overlay validates and consolidated contract has been regenerated.

### Remaining before M1.4 merge

1. run full CI on a normal commit after generated OpenAPI sync;
2. require green Backend quality, PostgreSQL lifecycle, OpenAPI, Frontend and Compose jobs;
3. if needed, fix only concrete CI findings without relaxing quality gates;
4. self-review PR #24 diff;
5. mark PR ready and squash-merge;
6. verify Issue #19 closes;
7. update `main/PROJECT_STATE.md` with final M1.4 merge SHA.

## Next after M1.4

**M1.5 — audit/outbox/observability foundation (Issue #20).**

Only after M1 foundation is complete do we move to M2 Fleet & Drivers business modules.

## Regulatory baseline

State verified on 15.09.2026. Canonical documents are under `docs/10-Legal/`.
Traceability: `source → MR decision → BR-* → API/DB/policy → AT-*`.

## Deferred — not blockers for M1

GPS/live monitoring, passenger accounting/e-ticketing, mobile driver app, payroll/accounting, fuel-card integration, parts warehouse, external route-passport integration, advanced analytics, additional non-primary document roles, final enterprise retention periods.

Deferred work cannot change frozen M0 invariants without ADR + impact review.

## Repository governance

- `docs/` — canonical Obsidian Vault;
- significant changes — branch + Pull Request;
- accepted ADR are not silently rewritten;
- Business Rule IDs: `BR-*`;
- Acceptance Test IDs: `AT-*`;
- secrets and production data are never stored in Git.
