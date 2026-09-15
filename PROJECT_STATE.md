# PROJECT_STATE

## Architecture baseline

Версія архітектури: **v1.3**

Зафіксовано:

- Modular Monolith.
- PostgreSQL як транзакційне джерело істини.
- `Trip` = окремий рейс.
- `Duty` = наряд / виробнича зміна, що містить 1..N рейсів.
- `Release` належить Duty.
- `Waybill` базово належить Duty і може містити 1..N рейсів.
- Plan і Fact розділені.
- Закриті фактичні дані мають immutable snapshots.
- Waybill має immutable versions.
- Correction workflow не відкриває закритий об'єкт повторно.
- Audit append-only.
- Critical state changes виконуються командами, а не довільним PATCH status.
- PostgreSQL exclusion constraints захищають від double-booking автобусів та водіїв.
- Optimistic locking (`row_version` / ETag) захищає від lost update.
- Idempotency-Key використовується для критичних повторюваних команд.
- Outbox закладений для інтеграцій.
- Tenant/company isolation є частиною моделі.

## Наступна архітектурна робота

1. MVP Definition Package.
2. Остаточний перелік MVP екранів і user flows.
3. OpenAPI MVP contract.
4. ERD та PostgreSQL DDL design review.
5. Deployment / backup / DR policy.
6. Definition of Done та acceptance suite.
7. Лише після freeze — Alembic migration #1 та перший FastAPI module.

## Repository governance baseline

- Documentation root doubles as Obsidian Vault: `docs/`.
- ADRs record architectural decisions; accepted ADRs are not rewritten to hide history.
- Stable Business Rule IDs introduced (`BR-*`).
- Stable Acceptance Test IDs introduced (`AT-*`).
- Traceability matrix introduced.
- Legal sources are tracked separately and must be verified before regulatory implementation freeze.
- Bootstrap backlog exists in `docs/12-Backlog`; GitHub Issues becomes the task-level tracker after repository publication.
