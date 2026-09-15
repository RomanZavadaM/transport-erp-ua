# PROJECT_STATE

## Архітектурний baseline

Версія архітектури: **v1.4**

Канонічна мова проєкту: **українська (`uk`)**. Похідні локалі: `en`, `es`, `fr`, `de`.

## Ключові рішення

- Modular Monolith.
- PostgreSQL — транзакційне джерело істини.
- `Trip != Duty`; один Duty містить 1..N Trips.
- `Release` належить Duty.
- `Waybill` базово належить Duty і може охоплювати 1..N Trips.
- Plan і Fact зберігаються окремо.
- CLOSED history не переписується: snapshots/versions + correction workflow.
- Audit та operational events — append-only.
- PostgreSQL EXCLUDE захищає від double-booking ресурсів.
- Optimistic locking + ETag/If-Match захищають від lost update.
- Idempotency-Key використовується для критичних повторюваних commands.
- Transactional outbox закладений для інтеграцій.
- Tenant/company isolation — частина DB model.

## Завершено в M0

### MVP Definition Package

- межі production MVP;
- наскрізний operational day;
- ролі та use cases;
- каталог екранів;
- production Definition of Done.

### API Contract Package

- `/api/v1` semantic endpoint catalog;
- explicit business command endpoints;
- DTO/schema rules;
- stable error catalog;
- permissions;
- concurrency/idempotency contract;
- transaction boundaries;
- machine-readable OpenAPI 3.1 draft.

### PostgreSQL Physical Schema v1

- 77 core tables;
- поля/типи для M0 domains;
- PK/FK/UNIQUE/CHECK/EXCLUDE;
- tenant-aware composite FK;
- RLS;
- immutable/append-only policy;
- index/partition strategy;
- restrictive delete policy;
- ERD v1;
- migration-readiness checklist.

### UX Flow / Wireframe Package

- Dispatcher Board;
- Release Workspace;
- Waybill Workspace;
- role workspaces/wireframes;
- navigation / information architecture;
- interaction patterns для conflict, stale data, blocking states, overflow/scroll, keyboard/copy-paste та destructive actions.

### Production Operations Package

- production topology: application node + data node + independent off-site backup/object-storage failure domain;
- Docker Compose baseline без Kubernetes;
- secrets/configuration policy;
- PostgreSQL backup + continuous WAL/PITR;
- object-storage backup/versioning;
- initial targets: DB RPO ≤ 15 хв, RTO ≤ 4 год; critical object RPO ≤ 1 год;
- monthly restore drills + quarterly DR exercises;
- disaster-recovery governance runbook;
- structured logs/metrics/health/alerts;
- system integrity checker;
- production-readiness checklist.

## Відкриті policy items `MR-*`

Див. `docs/02-Data/schema/09-Migration-Readiness.md`.

Перед rigid DDL/seed ще потрібно business/legal confirmation для:

- допустимих результатів медичного контролю;
- Waybill↔Duty policy/cardinality;
- crew policy;
- required/blocking document catalog;
- operational-day cutoff;
- Waybill numbering/reset policy;
- legal retention/object-lock policy.

## Наступні ворота Architecture Freeze

1. **Issue #6 — i18n resources/document locale contract**.
2. Regulatory/business review `MR-*` items.
3. Розширення traceability та M0 acceptance suite.
4. Фінальний Architecture Freeze review.
5. Лише після M0 freeze — Alembic migration #1 та перший FastAPI module.

## Repository governance

- `docs/` — канонічний Obsidian Vault.
- Українська — source of truth; переклади не створюють окремих вимог.
- accepted ADR не переписуються із приховуванням історії.
- Business Rule IDs: `BR-*`.
- Acceptance Test IDs: `AT-*`.
- значні зміни проходять branch + Pull Request.
- secrets та production data у Git не зберігаються.
