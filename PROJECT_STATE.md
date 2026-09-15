# PROJECT_STATE

## Поточний baseline

Архітектура: **architecture-v1.5**  
Статус архітектури: **M0 Architecture Freeze — FROZEN**  
Канонічна мова: **українська (`uk`)**; переклади: `en`, `es`, `fr`, `de`.

Поточний етап реалізації: **M1.5 — Audit / Outbox / Observability foundation**.

## Product scope — IMPORTANT

**TransportERP-UA проєктується насамперед як ERP одного автотранспортного підприємства**, а не як державна, регіональна чи multi-tenant SaaS-платформа для багатьох незалежних перевізників.

Основний контур продукту:

`підприємство → підрозділи/депо/колони → парк → водії → маршрути → розклад → наряди → випуск → рейси → повернення → паливо/пробіг → ТО/ремонт → документи → звітність`.

Можливість кількох `company_id`, tenant-context і RLS, уже реалізована в фундаменті, **не визначає бізнес-модель продукту**. Вона може залишатися як технічний захист/резерв для філій, юридично відокремлених підрозділів або майбутнього розширення, але не повинна ускладнювати UX, процеси чи бізнес-логіку одного підприємства.

Не проєктувати без окремого рішення:

- державний або регіональний верхній рівень;
- cross-company аналітику незалежних перевізників;
- SaaS billing/tenant onboarding;
- централізоване управління багатьма незалежними підприємствами;
- державний data lake або галузеву платформу.

Якщо будь-яка наявна архітектурна конструкція створює зайву складність для одного підприємства, її потрібно переглянути перед подальшим розвитком, а не виправдовувати потенційним SaaS/державним масштабом.

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
- RLS/company context залишаються технічним шаром ізоляції, але продуктова ціль — одне підприємство.
- Transactional outbox та integrity checker закладені в core.

## M0 — DONE

MVP, API contract, PostgreSQL physical design, UX, RBAC policy, i18n, testing/traceability, operations/DR та regulatory review завершені й frozen у `architecture-v1.5`.

## M1 — стан реалізації

### M1.1 Application skeleton + CI — DONE

Merged to `main` as `f85c6b9…`.

### M1.2 Consolidated OpenAPI — DONE

Merged to `main` as `27ac384…`.

### M1.3 Alembic migration #1 + PostgreSQL invariants — DONE

Merged to `main` as:

`d64c765b9ed6ee7acdf1add12fbf4ae26edeeba8`

Verified lifecycle:

`upgrade head → 12 PostgreSQL acceptance tests → downgrade base → upgrade head → schema verification`

Issue #18 closed.

### M1.4 Identity and access foundation — DONE

PR **#24** squash-merged to `main` as:

`7d17edf737cc344037bed3ee4ade6ecbb689b2cc`

Issue: **#19**.

Implemented:

- bounded context `identity/domain/application/infrastructure/api`;
- SQLAlchemy session factory and transaction-local tenant context via `SET LOCAL app.company_id`;
- Argon2id password hashing;
- opaque cryptographically-random browser session tokens;
- only SHA-256 session-token hash stored in PostgreSQL;
- HttpOnly session cookie;
- session-bound double-submit CSRF protection;
- production guard requiring secure cookies;
- login/session rotation/logout and revocation;
- user statuses `ACTIVE/SUSPENDED/DISABLED`;
- permission-based RBAC instead of hardcoded role-name authorization;
- effective permission resolution;
- users/roles/permission-catalog management foundation;
- reusable FastAPI `require_permission(...)` dependency;
- stable API error envelope and request-id;
- auth endpoints: login/refresh/logout/me/permissions;
- user create/list/get/patch/status/roles foundation;
- role create/list and permission catalog API;
- Alembic migration #2;
- full frozen permission catalog seed;
- global `ADMIN` template role;
- ADMIN has identity/settings/audit administration permissions but does **not** implicitly receive release/medical/technical business permissions;
- narrow PostgreSQL `SECURITY DEFINER` company resolver for login bootstrap under RLS;
- DB trigger rejecting cross-company role assignment;
- identity unit tests and real PostgreSQL/API acceptance tests;
- OpenAPI contract updated for cookie session, CSRF and identity endpoints.

Final M1.4 CI was fully green:

- Backend: Ruff + strict mypy + pytest;
- PostgreSQL: clean upgrade + acceptance tests + downgrade + re-upgrade + schema verification;
- OpenAPI: generation + validation + freshness;
- Frontend: ESLint + TypeScript + production build;
- Compose validation.

## M1.5 — NEXT / ACTIVE

GitHub Issue: **#20 — audit/outbox/observability foundation**.

Before implementing M1.5, re-check each planned mechanism against the **single-enterprise product scope** and avoid SaaS/state-scale complexity that has no concrete enterprise beneficiary.

Planned order:

1. append-only audit application service and writer;
2. transactional audit recording integrated with application transactions;
3. transactional outbox writer and event envelope;
4. worker-safe outbox claim/publish state using PostgreSQL locking semantics;
5. structured request/application logging with correlation/request IDs;
6. readiness endpoint with database dependency check;
7. metrics/health foundation without leaking sensitive payloads;
8. integrity-check runner foundation;
9. PostgreSQL/API tests proving audit immutability and audit/outbox atomicity;
10. CI green before merge.

After M1.5, M1 foundation is complete and the project can move to **M2 Fleet & Drivers** business modules.

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
