# PROJECT_STATE

## Архітектурний baseline

Версія архітектури: **v1.3**

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

## Мовна політика

- **Українська (`uk`) — основна, канонічна та нормативна мова проєкту.**
- Переклади підтримуються англійською (`en`), іспанською (`es`), французькою (`fr`) та німецькою (`de`).
- Архітектурні рішення, бізнес-правила, acceptance criteria та юридично значимі описи спочатку затверджуються українською.
- Переклади не є окремими джерелами вимог.
- У разі будь-якої розбіжності між перекладом і українським оригіналом пріоритет має український текст.
- Структура перекладів: `docs/i18n/<language>/...`.

## Наступна архітектурна робота

1. MVP Definition Package.
2. Остаточний перелік MVP екранів і user flows.
3. OpenAPI MVP contract.
4. ERD та PostgreSQL DDL design review.
5. Deployment / backup / DR policy.
6. Definition of Done та acceptance suite.
7. Лише після freeze — Alembic migration #1 та перший FastAPI module.

## Repository governance baseline

- `docs/` є канонічним Obsidian Vault.
- Основна документація у `docs/` ведеться українською.
- Переклади зберігаються під `docs/i18n/` і мають посилатися на канонічний український документ.
- ADR фіксують архітектурні рішення; accepted ADR не переписуються так, щоб приховати історію.
- Стабільні Business Rule ID використовують формат `BR-*`.
- Стабільні Acceptance Test ID використовують формат `AT-*`.
- Traceability matrix є частиною архітектурної документації.
- Законодавчі джерела ведуться окремо й перевіряються перед regulatory implementation freeze.
