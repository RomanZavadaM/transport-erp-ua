# Обмеження та інваріанти БД

Architecture-v1.6 має один набір business invariants і два physical profiles: Local SQLite та Central PostgreSQL.

Критичне правило не може існувати тільки як PostgreSQL-specific constraint, якщо воно потрібне локальному застосунку.

Пов’язані документи:

- [`schema/00-Conventions.md`](schema/00-Conventions.md)
- [`schema/07-RLS-Immutability-Indexes.md`](schema/07-RLS-Immutability-Indexes.md)
- [`schema/08-Foreign-Keys-and-Delete-Policy.md`](schema/08-Foreign-Keys-and-Delete-Policy.md)
- [`schema/09-Migration-Readiness.md`](schema/09-Migration-Readiness.md)

## Фундаментальні invariants

1. Один автобус не має overlapping ACTIVE assignments.
2. Один водій не має overlapping ACTIVE assignments.
3. Один Trip не має двох ACTIVE Duty memberships.
4. Active route/schedule versions не мають недопустимого overlap.
5. `schedule_run_id + service_date` генерує максимум один Trip.
6. Business document numbers унікальні в межах затвердженої numbering scope.
7. Historical snapshots/versions/events/audit не переписуються звичайним edit flow.
8. State changes підпорядковані state machine.
9. Local record з authority=`CENTRAL` не може бути змінений local business command.
10. Transfer не змінює authority до verified central ACK.
11. Transfer не стартує без explicit local operator approval.

## Local SQLite — механізми

- controlled application write transactions;
- FK;
- UNIQUE;
- CHECK;
- indexes;
- partial indexes, де доречно;
- optimistic locking через `row_version`;
- application overlap/current-state validation;
- triggers лише для фундаментальної immutability/authority defense-in-depth.

Для resource assignment local backend перечитує актуальний стан усередині write transaction і тільки після цього записує assignment.

## Central PostgreSQL — додаткові механізми

На central ті самі rules можуть підсилюватися:

- GiST exclusion constraints;
- range types;
- row locks;
- RLS;
- tenant-aware composite FK;
- DB roles/grants;
- partitioning після підтвердженої потреби.

Це defense-in-depth central profile, а не вимога Local Desktop.

## Half-open periods

Period semantics однакова на обох profiles: `[from,to)`.

Тому:

- `08:00–10:00`;
- `10:00–12:00`

не конфліктують.

Local зберігає from/to окремо та перевіряє overlap application query. Central може використовувати range/exclusion.

## Availability

Попередня availability query не є остаточною гарантією.

Остаточна перевірка відбувається під час mutation transaction:

- Local SQLite — current-state recheck + coordinated write transaction;
- Central PostgreSQL — те саме + DB-specific exclusion/locks за потреби.

## Delete policy

Business history default — RESTRICT/NO ACTION semantics.

Operational помилки виправляються lifecycle/correction workflow, а не фізичним видаленням історії.

## Company/RLS

Local node зазвичай працює в одному enterprise context і не емулює RLS.

Central PostgreSQL може використовувати RLS/composite FK для company isolation, якщо central deployment цього потребує.

## Authority invariant

Перед будь-яким local UPDATE/DELETE backend перевіряє authority.

`CENTRAL` → mutation rejected.

SQLite trigger може дублювати це правило для critical aggregate tables, але UI не є гарантом.

## Migration gate

До M2 Local SQLite повинна пройти acceptance tests з `schema/09-Migration-Readiness.md`, включно з transfer approval/ACK/read-only і backup/restore.
