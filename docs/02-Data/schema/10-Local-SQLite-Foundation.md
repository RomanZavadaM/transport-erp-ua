# Local SQLite Foundation — M1.5

Статус: **implementation target for architecture-v1.6**

Цей документ визначає **що реально створюємо в SQLite у M1.5**. Він не намагається наперед переписати всі майбутні M2–M8 таблиці.

## 1. SQLite database

Default logical file name:

`transporterp.db`

Actual path визначає platform data-directory service.

На кожному connection/startup обов’язково перевіряється:

```sql
PRAGMA foreign_keys = ON;
```

Journal/synchronous/busy-timeout values затверджуються acceptance tests після forced-crash tests.

## 2. UUID та timestamps

Local physical conventions:

- UUID → canonical lowercase text UUID;
- timestamp → UTC ISO-8601 text through persistence adapter;
- boolean → INTEGER `0|1`;
- JSON payload → TEXT serialized JSON + application schema validation.

Не використовувати floating-point для exact business money/fuel values у майбутніх domain tables без окремого tested mapping.

## 3. Existing identity foundation

M1.4 identity concepts переносяться на SQLite local profile без RLS/PostgreSQL roles.

Local minimum:

- `companies`;
- `company_settings`;
- `users`;
- `user_sessions`;
- `roles`;
- `permissions`;
- `user_roles`;
- `role_permissions`;
- `api_idempotency_keys` там, де existing API contract його використовує.

Local node працює в одному active company context. `company_id` лишається в model для сумісності/central transfer, але RLS не емулюється.

## 4. local_nodes

Одна installation identity на local data set.

```text
local_nodes
-----------
id                  TEXT PK UUID
company_id          TEXT NOT NULL
name                TEXT NOT NULL
created_at          TEXT NOT NULL UTC
created_by          TEXT NULL
central_enabled     INTEGER NOT NULL DEFAULT 0 CHECK 0|1
active              INTEGER NOT NULL DEFAULT 1 CHECK 0|1
```

Правило M1.5: один active node row на local DB.

Node id не регенерується при звичайному application update/reinstall поверх існуючих data.

## 5. transfer_requests

Запит/правило може лише запропонувати передачу.

```text
transfer_requests
-----------------
id                  TEXT PK UUID
origin              TEXT NOT NULL CHECK MANUAL|CENTRAL_REQUEST|RULE
external_request_id TEXT NULL
rule_code           TEXT NULL
requested_at        TEXT NOT NULL
requested_by        TEXT NULL
summary             TEXT NULL
status              TEXT NOT NULL CHECK OPEN|CONVERTED|REJECTED|CANCELLED
handled_by          TEXT NULL
handled_at          TEXT NULL
metadata_json       TEXT NOT NULL DEFAULT '{}'
```

`CENTRAL_REQUEST` не означає approval.

## 6. transfer_batches

```text
transfer_batches
----------------
id                  TEXT PK UUID
origin_node_id      TEXT NOT NULL FK local_nodes
request_id          TEXT NULL FK transfer_requests
status              TEXT NOT NULL
prepared_reason     TEXT NOT NULL CHECK MANUAL|CENTRAL_REQUEST|RULE
prepared_at         TEXT NOT NULL
prepared_by         TEXT NULL
approved_at         TEXT NULL
approved_by         TEXT NULL
payload_checksum    TEXT NULL
started_at          TEXT NULL
last_attempt_at     TEXT NULL
attempt_count       INTEGER NOT NULL DEFAULT 0 CHECK >=0
last_error_code     TEXT NULL
last_error_message  TEXT NULL
acknowledged_at     TEXT NULL
central_ack_id      TEXT NULL
cancelled_at        TEXT NULL
cancelled_by        TEXT NULL
row_version         INTEGER NOT NULL DEFAULT 1
```

Allowed status:

- `PENDING_APPROVAL`;
- `TRANSFERRING`;
- `FAILED`;
- `ACKNOWLEDGED`;
- `CANCELLED`.

Constraints/application guards:

- `TRANSFERRING|FAILED|ACKNOWLEDGED` require `approved_at` + `approved_by`;
- `ACKNOWLEDGED` requires `central_ack_id` + `acknowledged_at`;
- approval checksum is immutable while batch is active;
- retry increments `attempt_count`.

Indexes:

- `(status, prepared_at)`;
- `(request_id)`;
- `(central_ack_id)` optional unique when not null.

## 7. transfer_items

```text
transfer_items
--------------
transfer_batch_id   TEXT NOT NULL FK transfer_batches ON DELETE CASCADE only while draft/pending policy permits
entity_type         TEXT NOT NULL
entity_id           TEXT NOT NULL UUID
entity_version      INTEGER NOT NULL
payload_checksum    TEXT NOT NULL
transfer_order      INTEGER NOT NULL DEFAULT 0
PRIMARY KEY (transfer_batch_id, entity_type, entity_id)
```

Important:

- item references aggregate/root entity;
- після approval склад items immutable;
- dependency inclusion робить application transfer builder.

## 8. transfer_delivery_queue

Один local worker/process достатній.

```text
transfer_delivery_queue
-----------------------
id                  TEXT PK UUID
transfer_batch_id   TEXT NOT NULL UNIQUE FK transfer_batches
created_at          TEXT NOT NULL
available_at        TEXT NOT NULL
attempt_count       INTEGER NOT NULL DEFAULT 0
last_attempt_at     TEXT NULL
last_error_code     TEXT NULL
last_error_message  TEXT NULL
completed_at        TEXT NULL
```

Index:

`(completed_at, available_at)`.

No Redis/Kafka.

## 9. Authority mixin for transferable aggregate roots

Майбутні M2+ transferable aggregate root tables отримують стандартні fields:

```text
authority               TEXT NOT NULL DEFAULT 'LOCAL' CHECK LOCAL|CENTRAL
transfer_lock_batch_id   TEXT NULL
central_version          INTEGER NULL
central_ack_id           TEXT NULL
central_synced_at        TEXT NULL
```

Rules:

- новий local record → `authority=LOCAL`;
- `PENDING_APPROVAL` не змінює authority;
- local approval sets `transfer_lock_batch_id`, authority still `LOCAL`;
- failed delivery → authority still `LOCAL`;
- cancelled failed transfer clears transfer lock;
- verified ACK → authority=`CENTRAL`, transfer lock cleared, central metadata recorded;
- local business mutation requires authority=`LOCAL` and no active transfer lock;
- system sync path may update a `CENTRAL` local copy from central version.

M1.5 prototype should implement this mixin on at least one small fixture/test aggregate before M2 tables exist.

## 10. audit_log

Local physical minimum:

```text
audit_log
---------
id                  TEXT PK UUID
occurred_at         TEXT NOT NULL
actor_user_id       TEXT NULL
node_id             TEXT NOT NULL
request_id          TEXT NULL
correlation_id      TEXT NULL
action              TEXT NOT NULL
entity_type         TEXT NOT NULL
entity_id           TEXT NULL
source              TEXT NOT NULL
reason              TEXT NULL
before_json         TEXT NULL
after_json          TEXT NULL
changed_fields_json TEXT NULL
metadata_json       TEXT NOT NULL DEFAULT '{}'
```

Indexes:

- `(occurred_at)`;
- `(entity_type, entity_id, occurred_at)`;
- `(actor_user_id, occurred_at)`;
- `(request_id)`.

No local partitioning.

Normal application code не UPDATE/DELETE audit rows.

## 11. backup_runs

```text
backup_runs
-----------
id                  TEXT PK UUID
started_at          TEXT NOT NULL
completed_at        TEXT NULL
status              TEXT NOT NULL CHECK RUNNING|SUCCESS|FAILED
backup_path         TEXT NOT NULL
manifest_path       TEXT NULL
db_checksum         TEXT NULL
file_count          INTEGER NULL
backup_size_bytes   INTEGER NULL
app_version         TEXT NOT NULL
schema_version      TEXT NOT NULL
error_code          TEXT NULL
error_message       TEXT NULL
created_by          TEXT NULL
```

UI використовує цю таблицю для `last successful backup`.

## 12. system_integrity_alerts

```text
system_integrity_alerts
-----------------------
id                  TEXT PK UUID
check_code          TEXT NOT NULL
severity            TEXT NOT NULL CHECK INFO|WARNING|ERROR|CRITICAL
entity_type         TEXT NULL
entity_id           TEXT NULL
detected_at         TEXT NOT NULL
details_json        TEXT NOT NULL DEFAULT '{}'
status              TEXT NOT NULL CHECK OPEN|ACKNOWLEDGED|RESOLVED
acknowledged_at     TEXT NULL
acknowledged_by     TEXT NULL
resolved_at         TEXT NULL
resolved_by         TEXT NULL
resolution_comment  TEXT NULL
```

Indexes:

- `(status, severity, detected_at)`;
- `(check_code, detected_at)`.

## 13. app_meta / schema state

Alembic/version table лишається canonical migration marker.

Окремо можна мати lightweight application metadata only if реально потрібно для:

- node initialization completed;
- data-layout version;
- last successful startup checks.

Не дублювати Alembic revision без потреби.

## 14. Central receive foundation

Central PostgreSQL M1.5 додає щонайменше:

```text
registered_nodes
received_transfer_batches
```

`received_transfer_batches` має UNIQUE по `(origin_node_id, transfer_batch_id)` та зберігає:

- checksum;
- received_at;
- ack_id;
- processing result/version metadata.

Повтор identical batch повертає existing ACK.

Той самий batch id з іншим checksum → hard error + audit/integrity alert.

## 15. Що НЕ створюємо в SQLite M1.5 наперед

До відповідного milestone не переносимо всі майбутні 77 domain tables лише заради формального parity.

Не створюємо наперед:

- Fleet/Driver full tables — M2;
- Routes/Schedules/Trips — M3;
- Duty assignments — M4;
- Release/check full schema — M5;
- Waybill/fuel/maintenance full schema — M6+ за roadmap;
- audit partitions;
- job cluster tables;
- Redis/Kafka integration metadata;
- S3-only metadata, якщо local filesystem достатній.

## 16. M1.5 migration acceptance

SQLite migration passes only if automated tests prove:

1. clean file creates successfully;
2. identity login/RBAC works on SQLite;
3. FK is enabled;
4. node id persists across restart/update;
5. request/rule creates only pending transfer proposal;
6. transfer cannot enter `TRANSFERRING` without local operator approval;
7. approved batch locks test aggregate but keeps authority=`LOCAL`;
8. failed delivery does not change authority;
9. identical retry is stable;
10. valid ACK changes authority to `CENTRAL`;
11. local business mutation of `CENTRAL` test aggregate fails;
12. audit captures prepare/approve/fail/ACK/authority transition;
13. backup/restore preserves node id, users, audit, transfer state and checksums;
14. application restarts cleanly after forced process termination.
