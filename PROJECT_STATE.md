# PROJECT_STATE

## Архітектурний baseline

Версія архітектури: **v1.4**  
Статус: **M0 Architecture Freeze — regulatory review completed, final freeze review pending**.

Канонічна мова проєкту: **українська (`uk`)**. Похідні локалі: `en`, `es`, `fr`, `de`.

## Ключові рішення

- Modular Monolith.
- PostgreSQL — транзакційне джерело істини.
- `Trip != Duty`; один Duty містить 1..N Trips.
- `Release` належить Duty.
- `Waybill` — versioned enterprise operational/accounting document, базово пов'язаний з Duty і 1..N Trips; exact document role/cardinality є policy, а не застарілим hardcoded statutory assumption.
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

- application/data/off-site failure domains;
- Docker Compose baseline;
- secrets/configuration policy;
- PostgreSQL backup + continuous WAL/PITR;
- object-storage backup/versioning;
- initial RPO/RTO targets;
- restore drills та DR exercises;
- observability/alerts;
- system integrity checker;
- production-readiness checklist.

### i18n Contract Package

- `uk` — default/canonical locale;
- locale resolution і fallback;
- stable semantic UI resource keys;
- API/error/permission/state codes не локалізуються;
- formatting/pluralization/layout rules;
- document/PDF locale + template version policy;
- historical PDF не змінюється при зміні UI locale;
- translation governance/statuses;
- localization test matrix для `uk/en/es/fr/de`.

### Regulatory / Business Review

Перевірено та зафіксовано станом на **15.09.2026**:

- Закон України «Про автомобільний транспорт» №2344-III;
- медичний контроль — наказ №65/80;
- технічний контроль — наказ №974;
- робочий час/відпочинок — Положення №340 з актуальними змінами;
- новий електронний route-passport workflow — наказ №1473;
- retention sources — Перелік №578/5 та Податковий кодекс, ст. 44.

`MR-001..MR-007` переведені з невизначеностей у confirmed/context/internal/legal policy decisions.

Основні корекції:

- medical result для щозмінного check: `FIT/UNFIT`;
- `FIT_WITH_RESTRICTIONS` не входить у rigid M0 medical state set;
- technical checker — qualified/authorized actor, не hardcoded job title;
- потрібне окреме driver pre-departure technical evidence;
- required documents визначаються transport/service context + rule version;
- crew model підтримує кількох водіїв;
- Waybill не моделюється як універсально обов'язковий державний «дорожній лист»;
- retention є class-based, із legal-hold/extension semantics;
- route passport розглядається як future external government integration boundary.

Business Rule Catalog, Traceability Matrix та Acceptance Criteria розширені відповідними `BR-*` / `AT-*`.

## Документи regulatory baseline

- `docs/10-Legal/Regulatory-Register.md`;
- `docs/10-Legal/Regulatory-Review-2026-09.md`;
- `docs/10-Legal/MR-Decision-Register.md`;
- `docs/10-Legal/Regulatory-Change-Log.md`;
- `docs/02-Data/schema/09-Migration-Readiness.md`.

## Що лишилося до M0 Architecture Freeze

1. Final cross-document consistency review.
2. Перевірити, що regulatory corrections відображені у physical schema/API/UX без суперечностей.
3. Сформувати M0 Freeze Checklist та explicit deferred-items register.
4. Підняти architecture baseline до freeze version після review.
5. Лише після прийняття freeze — Alembic migration #1 та application skeleton.

## Repository governance

- `docs/` — канонічний Obsidian Vault.
- Українська — source of truth; переклади не створюють окремих вимог.
- accepted ADR не переписуються із приховуванням історії.
- Business Rule IDs: `BR-*`.
- Acceptance Test IDs: `AT-*`.
- значні зміни проходять branch + Pull Request.
- secrets та production data у Git не зберігаються.
