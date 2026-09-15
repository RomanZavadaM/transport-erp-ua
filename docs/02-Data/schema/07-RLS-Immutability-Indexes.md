# PostgreSQL Schema — RLS, Immutability, Indexes & Partitioning

Статус: **M0 physical design draft**

## 1. Tenant isolation

Основний tenant key — `company_id`.

Він присутній у всіх основних operational/business tables навіть там, де теоретично міг би бути отриманий через parent relation. Це свідома денормалізація для:

- RLS;
- tenant-aware composite FK;
- індексів;
- reporting;
- захисту від cross-company programming error.

## 2. Tenant-aware foreign keys

Критичні parent tables мають:

`UNIQUE (company_id, id)`.

Child relation використовує:

`FOREIGN KEY (company_id, parent_id) REFERENCES parent(company_id,id)`.

Обов'язково для relations, де cross-tenant помилка матиме серйозний наслідок:

- vehicles ↔ depots;
- drivers ↔ depots;
- users ↔ drivers;
- route_versions ↔ routes;
- route_stops ↔ route_versions/stops;
- schedules ↔ routes;
- schedule_versions ↔ schedules/route_versions;
- trips ↔ route_versions/schedule_runs;
- duty_trips ↔ duties/trips;
- duty assignments ↔ duties/vehicles/drivers;
- releases ↔ duties;
- checks ↔ releases + subject;
- waybills ↔ duties;
- fuel ↔ vehicles/duties/trips/waybills;
- defects/maintenance/repairs ↔ vehicles;
- audit/outbox/report exports ↔ company-scoped actors/entities where direct FK is practical.

Polymorphic audit/entity references не мають universal FK, але company scope завжди зберігається.

## 3. PostgreSQL RLS

RLS вмикається для tenant-scoped business tables після bootstrap/migration creation.

Runtime transaction встановлює company context transaction-locally, наприклад application-defined setting:

`SET LOCAL app.company_id = '<uuid>'`.

Policy concept:

`company_id = current_setting('app.company_id', true)::uuid`.

Runtime role:

- не superuser;
- не table owner;
- не `BYPASSRLS`.

Якщо company context відсутній, tenant rows не повинні ставати доступними за default-fail policy.

## 4. System/global reference rows

Таблиці, що можуть мати global rows (`company_id IS NULL`), наприклад:

- permissions;
- деякі system document/check types/templates;
- global reference dictionaries,

читаються через окремо визначену policy/view.

Tenant user не отримує write access до global system rows.

## 5. Service identities

Background worker використовує окрему DB/service identity.

Він не повинен автоматично мати unrestricted cross-tenant access. Для cross-company scheduled jobs застосовується контрольований service context або окремий privileged worker role з audit/monitoring, а не звичайний runtime connection.

## 6. Immutable / append-only tables

Повністю append-only після INSERT:

- `audit_log`;
- `trip_events`;
- `duty_events`;
- `trip_actual_snapshots`;
- finalized `waybill_versions` content;
- `release_rule_evaluations`;
- `audit_partition_seals`;
- completed historical correction evidence.

Для них runtime role:

- `SELECT` за permissions/RLS;
- `INSERT` через application service;
- без `DELETE`;
- без `UPDATE`, крім чітко виділених technical lifecycle fields, якщо вони фізично відокремлені або whitelist-нуті.

## 7. Immutability triggers

Defense-in-depth trigger використовується там, де одних grants недостатньо через operational tooling/migration mistakes.

Conceptual trigger:

- `BEFORE UPDATE OR DELETE`;
- якщо session role є runtime/business role → raise exception;
- migration/maintenance role може виконувати контрольовані операції лише через change procedure/runbook.

Не створювати trigger spaghetti для кожного business rule; triggers тут лише для фундаментальної immutability.

## 8. Completed checks

`pre_trip_checks` до completion є stateful row. Після `PASSED/FAILED` business fields стають immutable.

Виправлення:

- original check не UPDATE-иться;
- створюється `pre_trip_check_invalidations`;
- потім новий check.

DB trigger/application guard може блокувати update completed row за винятком explicitly allowed technical metadata, якщо таке взагалі буде потрібне.

## 9. Closed aggregates

Для `trips`, `duties`, `waybills` aggregate root row має окремі lifecycle fields, тому сам row технічно може змінюватися при correction pointer update.

Але після terminal state забороняється зміна historical core fields:

- plan identifiers/times, що вже є історичною основою;
- original close timestamps/actor без correction workflow;
- document number;
- closed snapshot/version content.

Correction змінює лише effective-version pointer/metadata через спеціальну command.

## 10. Critical indexes — organization/identity

- `users(company_id,status)`;
- unique `users(company_id,username)`;
- unique partial email;
- `user_sessions(user_id,expires_at)`;
- partial active session expiration;
- idempotency unique scope key;
- idempotency `(expires_at)` cleanup index.

## 11. Critical indexes — fleet/drivers

Vehicles:

- unique fleet number;
- unique registration number;
- unique VIN partial;
- `(company_id,lifecycle_status)`;
- `(company_id,depot_id,lifecycle_status)`.

Documents:

- `(company_id,vehicle_id,document_type_id)`;
- `(company_id,valid_until)`;
- corresponding driver indexes.

Odometer:

- `(vehicle_id,recorded_at DESC)`;
- confirmed partial index.

Drivers:

- unique personnel number;
- `(company_id,employment_status)`;
- `(company_id,default_depot_id,employment_status)`.

## 12. Critical indexes — planning

- unique route number;
- GiST exclusion on route version valid period;
- route stops ordered index;
- GiST exclusion on schedule version valid period;
- unique `(schedule_run_id,service_date)` for generated Trip;
- trips `(company_id,service_date)`;
- trips `(company_id,status,service_date)`;
- trips `(route_version_id,service_date)`;
- trips `(planned_departure_at)`.

## 13. Critical indexes — dispatch/release

Duty:

- `(company_id,service_date)`;
- `(company_id,status,service_date)`;
- `(company_id,depot_id,service_date)`.

Assignments:

- GiST exclusion indexes є головними conflict indexes;
- btree `(company_id,duty_id)`;
- btree `(company_id,vehicle_id)` / `(company_id,driver_id)`.

Release:

- UNIQUE duty_id;
- check queries `(release_id,check_type,completed_at DESC)`;
- evaluations `(release_id,evaluation_batch_id)`;
- partial unique positive authorization.

## 14. Critical indexes — documents/fuel/maintenance

Waybill:

- unique `(company_id,full_number)`;
- `(company_id,status,created_at)`;
- versions `(waybill_id,version_no DESC)`.

Fuel:

- `(company_id,vehicle_id,operation_at)`;
- `(company_id,operation_at)`;
- duty/waybill refs.

Defects:

- `(vehicle_id,status)`;
- partial blocking-open defect index.

Repairs:

- `(vehicle_id,status)`;
- partial blocking-operation index.

## 15. Audit partitioning

`audit_log` проектується як range-partitioned за `occurred_at`.

Рекомендований initial cadence: monthly partitions.

Причини:

- predictable retention/archive operations;
- локальні indexes;
- швидший time-range pruning;
- простіше sealing/archive.

Partition creation має бути автоматизоване operations job/migration policy завчасно.

Відсутність майбутньої partition не повинна ламати production insert: або default partition, або гарантоване precreation. Остаточний механізм затверджується Issue #5 operations design.

## 16. Trip/Duty events partitioning

Для MVP event volume очікується помірним, тому вони можуть стартувати unpartitioned.

Коли volume виправдає partitioning, migration може partition by occurred_at без зміни domain contract.

GPS positions від початку проектуються окремо й не повинні перевантажувати `trip_events`.

## 17. Outbox indexes

Partial index:

`WHERE published_at IS NULL` по `(created_at)`.

Worker query використовує bounded batch + `FOR UPDATE SKIP LOCKED`.

Не створювати надмірні indexes по JSON payload.

## 18. JSONB indexes

GIN indexes на JSONB додаються лише після підтвердженого query pattern.

Не індексувати `snapshot`, `audit before/after`, `payload` “про всяк випадок”.

## 19. pg_stat_statements / index review

Production index review виконується за:

- `pg_stat_statements`;
- `EXPLAIN (ANALYZE, BUFFERS)`;
- actual slow query telemetry.

M0 фіксує mandatory correctness/primary operational indexes, але не намагається вгадати всі оптимізації наперед.

## 20. Lock ordering

Canonical lock order для multi-aggregate critical transactions:

1. Duty;
2. Trips у deterministic order (`ORDER BY id`);
3. vehicle/driver resource state/assignment rows;
4. Release;
5. Waybill;
6. Number Sequence.

Новий application service, який порушує цей порядок, потребує concurrency review.

## 21. Isolation level

Default: `READ COMMITTED`.

Correctness отримуємо через:

- row locks;
- unique constraints;
- exclusion constraints;
- FK/check constraints;
- optimistic locking.

`SERIALIZABLE` — точково для складної planning operation після окремого benchmark/design review.

## 22. Deadlock/serialization retry

Runtime може bounded-retry transient DB failure лише якщо command side effects повністю transactional/idempotent.

Retry не повинен створювати duplicate audit/outbox/document artifacts.

## 23. DB role grants summary

### migration_role

- owns/migrates schema;
- no normal application use.

### app_runtime_role

- DML тільки потрібних tables;
- RLS enforced;
- no DDL;
- no UPDATE/DELETE immutable tables.

### reporting_role

- SELECT на views/materialized/read model;
- no operational mutation.

### backup_role

- privileges only sufficient for backup tooling.

## 24. Integrity checks after migration

Migration CI повинна перевіряти:

- всі expected constraints/indexes exist;
- RLS enabled where required;
- runtime grants do not include prohibited operations;
- clean install schema;
- upgrade path from previous release;
- rollback/recovery strategy documented for destructive migrations.
