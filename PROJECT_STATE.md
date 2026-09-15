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
- database integrity principles;
- repository/Obsidian structure;
- Business Rule IDs, Acceptance IDs і traceability foundation;
- multilingual architecture;
- **MVP Definition Package**:
  - межі production MVP;
  - наскрізний operational day;
  - ролі та use cases;
  - каталог MVP екранів;
  - production Definition of Done.

## Мовна політика

- **Українська (`uk`) — основна, канонічна та нормативна мова проєкту.**
- Переклади підтримуються англійською (`en`), іспанською (`es`), французькою (`fr`) та німецькою (`de`).
- Архітектурні рішення, бізнес-правила, acceptance criteria та юридично значимі описи спочатку затверджуються українською.
- Переклади не є окремими джерелами вимог.
- У разі будь-якої розбіжності між перекладом і українським оригіналом пріоритет має український текст.
- Структура перекладів: `docs/i18n/<language>/...`.
- API error codes і domain status values залишаються стабільними технічними кодами незалежно від locale.

## Наступні ворота Architecture Freeze

1. **Issue #2 — OpenAPI MVP contract**: endpoints, DTO, permissions, idempotency, concurrency/error semantics.
2. **Issue #3 — PostgreSQL physical schema review**: повний DDL design до Alembic migration #1.
3. Issue #4 — деталізувати UX flows/wireframes на основі затвердженого Screen Catalog.
4. Issue #5 — production topology, backup/restore і DR.
5. Issue #6 — деталізувати i18n resources/document locale contract.
6. Розширити acceptance suite і regulatory review для MVP.
7. Лише після M0 freeze — Alembic migration #1 та перший FastAPI module.

## Repository governance baseline

- `docs/` є канонічним Obsidian Vault.
- Основна документація у `docs/` ведеться українською.
- Переклади зберігаються під `docs/i18n/` і мають посилатися на канонічний український документ.
- ADR фіксують архітектурні рішення; accepted ADR не переписуються так, щоб приховати історію.
- Стабільні Business Rule ID використовують формат `BR-*`.
- Стабільні Acceptance Test ID використовують формат `AT-*`.
- Traceability matrix є частиною архітектурної документації.
- Законодавчі джерела ведуться окремо й перевіряються перед regulatory implementation freeze.
- GitHub Issues є task-level backlog для M0 Architecture Freeze.
- Значні зміни документації після bootstrap проходять через branch + Pull Request.