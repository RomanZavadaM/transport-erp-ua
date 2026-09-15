# Обмеження та інваріанти PostgreSQL

Критичні інваріанти забезпечуються PostgreSQL, а не лише application code.

Цей файл є коротким оглядом. Повний physical design:

- [`schema/00-Conventions.md`](schema/00-Conventions.md)
- [`schema/07-RLS-Immutability-Indexes.md`](schema/07-RLS-Immutability-Indexes.md)
- [`schema/08-Foreign-Keys-and-Delete-Policy.md`](schema/08-Foreign-Keys-and-Delete-Policy.md)
- [`schema/09-Migration-Readiness.md`](schema/09-Migration-Readiness.md)

## Фундаментальні DB invariants

1. Один автобус не має overlapping ACTIVE assignments.
2. Один водій не має overlapping ACTIVE assignments.
3. Один Trip не може мати два ACTIVE Duty memberships.
4. ACTIVE route versions одного Route не перекривають validity period.
5. ACTIVE schedule versions одного Schedule не перекривають validity period.
6. Регулярний `schedule_run_id + service_date` генерує максимум один Trip.
7. Business document numbers є унікальними.
8. Tenant-aware relation не може послатися на row іншої company.
9. Historical snapshots/versions/events/audit не можуть бути тихо UPDATE/DELETE runtime role.
10. Critical state changes додатково обмежені domain state machine та DB protection там, де це фундаментальний invariant.

## Основні механізми

- restrictive FK delete policy;
- unique/partial unique constraints;
- CHECK constraints;
- `daterange` для version validity;
- `tstzrange` для resource periods;
- GiST exclusion constraints;
- optimistic locking через `row_version`;
- short row locks для critical transactions;
- append-only grants/triggers;
- Row Level Security;
- tenant-aware composite FK;
- partitioning audit history;
- transaction-local tenant context.

## Half-open periods

Assignment ranges використовують `[from,to)`.

Тому:

- `[08:00,10:00)`;
- `[10:00,12:00)`

не перекриваються, а `[09:59,11:00)` із першим/другим — конфліктує відповідно.

## Availability

Frontend/backend availability query є лише попередньою інформацією. Остаточна гарантія під час concurrent allocation — database transaction + exclusion constraint.

## Delete policy

Для business history default — `RESTRICT/NO ACTION`.

Cascade не використовується для знищення Vehicle/Driver/Trip/Duty/Release/Waybill history. Operational помилка виправляється business state/correction workflow.

## RLS

Runtime role працює з company-scoped rows через RLS і не має `BYPASSRLS`. Cross-company integrity додатково захищається composite foreign keys.

## Migration gate

До Alembic migration #1 physical design проходить checklist [`schema/09-Migration-Readiness.md`](schema/09-Migration-Readiness.md). Нормативні policy-коди не повинні бути вигадані лише для того, щоб швидше написати constraint/seed.