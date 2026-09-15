# PROJECT_STATE

## Архітектурний baseline

Версія архітектури: **v1.4**

Зафіксовано:

- Modular Monolith.
- PostgreSQL як транзакційне джерело істини.
- `Trip` = окремий рейс.
- `Duty` = наряд / виробнича зміна, що містить 1..N рейсів.
- `Release` належить Duty.
- `Waybill` базово належить Duty і може містити 1..N рейсів.
- План і факт розділені.
- Закриті фактичні дані мають immutable snapshots.
- Waybill має immutable versions.
- Correction workflow не відкриває закритий об'єкт повторно.
- Audit append-only.
- Критичні зміни станів виконуються командами, а не довільним PATCH status.
- PostgreSQL exclusion constraints захищають від double-booking автобусів та водіїв.
- Optimistic locking (`row_version` / ETag) захищає від lost update.
- Idempotency-Key використовується для критичних повторюваних команд.
- Outbox закладений для інтеграцій.
- Tenant/company isolation є частиною моделі.
- ADR-0006 зафіксував українську як канонічну мову та i18n `uk/en/es/fr/de`.

## Завершено в M0

- первинний domain/architecture baseline;
- state-machine та concurrency principles;
- repository/Obsidian structure;
- Business Rule IDs, Acceptance IDs і traceability foundation;
- multilingual architecture;
- **MVP Definition Package**:
  - межі production MVP;
  - наскрізний operational day;
  - ролі та use cases;
  - каталог MVP екранів;
  - production Definition of Done;
- **API Contract Package**:
  - semantic endpoint catalog `/api/v1`;
  - DTO/schema rules;
  - stable error catalog;
  - permission catalog;
  - concurrency/idempotency contract;
  - transaction boundaries;
  - machine-readable OpenAPI 3.1 draft;
- **PostgreSQL Physical Schema v1**:
  - 77 core tables;
  - exact fields/types for M0 domains;
  - PK/FK/UNIQUE/CHECK/EXCLUDE strategy;
  - tenant-aware composite FK;
  - RLS policy;
  - immutable/append-only policy;
  - index/partition strategy;
  - restrictive delete policy;
  - ERD v1;
  - migration-readiness checklist.

## Відкриті policy items перед rigid DDL/seed

Позначені як `MR-*` у `docs/02-Data/schema/09-Migration-Readiness.md`:

- точний допустимий набір результатів медичного контролю;
- остаточна cardinality/типізація Waybill на Duty;
- crew policy для ролей водіїв усередині одного Duty;
- нормативний каталог required/blocking документів;
- operational-day cutoff policy;
- формат/скидання нумерації Waybill;
- retention/object-lock policy.

Це не архітектурні прогалини: вони навмисно не фіксуються припущенням до business/legal review.

## Мовна політика

- **Українська (`uk`) — основна, канонічна та нормативна мова проєкту.**
- Переклади підтримуються англійською (`en`), іспанською (`es`), французькою (`fr`) та німецькою (`de`).
- Архітектурні рішення, бізнес-правила, acceptance criteria та юридично значимі описи спочатку затверджуються українською.
- Переклади не є окремими джерелами вимог.
- У разі розбіжності пріоритет має український текст.
- API error codes і domain status values залишаються стабільними технічними кодами незалежно від locale.

## Наступні ворота Architecture Freeze

1. **Issue #4 — UX flows / wireframes** на основі Screen Catalog, Operational Day та API contract.
2. **Issue #5 — production topology, backup/restore та DR**.
3. **Issue #6 — деталізація i18n resources/document locale contract**.
4. Regulatory/business review `MR-*` items та розширення traceability.
5. Фінальний M0 acceptance review.
6. Лише після M0 freeze — Alembic migration #1 та перший FastAPI module.

## Repository governance baseline

- `docs/` є канонічним Obsidian Vault.
- Основна документація у `docs/` ведеться українською.
- Переклади зберігаються під `docs/i18n/`.
- Accepted ADR не переписуються так, щоб приховати історію.
- Stable Business Rule ID: `BR-*`.
- Stable Acceptance Test ID: `AT-*`.
- Traceability matrix є частиною архітектурної документації.
- Законодавчі джерела ведуться окремо й перевіряються перед regulatory implementation freeze.
- GitHub Issues є task-level backlog для M0.
- Значні зміни після bootstrap проходять через branch + Pull Request.