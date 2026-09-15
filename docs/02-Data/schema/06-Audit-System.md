# PostgreSQL Schema — Audit, Outbox, Reports & Integrity

# Audit

## audit_log

Append-only canonical audit trail.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| occurred_at | timestamptz | NOT NULL |
| actor_user_id | uuid | NULL |
| actor_role | varchar(120) | NULL snapshot/context |
| action | varchar(120) | NOT NULL |
| entity_type | varchar(80) | NOT NULL |
| entity_id | uuid | NULL |
| request_id | uuid | NOT NULL |
| correlation_id | uuid | NULL |
| source | varchar(40) | NOT NULL |
| ip_address | inet | NULL |
| user_agent | text | NULL |
| reason | text | NULL |
| before_data | jsonb | NULL |
| after_data | jsonb | NULL |
| changed_fields | jsonb | NULL |
| metadata | jsonb | NOT NULL DEFAULT `{}` |
| entry_hash | char(64) | NULL |

Rules:

- partition by RANGE(`occurred_at`) monthly after initial migration design;
- runtime app role: `INSERT`, permitted `SELECT`, no UPDATE/DELETE;
- sensitive values must be redacted/masked before insert according to audit policy;
- actor may be NULL for trusted system processes, but `source` and service identity metadata must identify origin.

Indexes per partition:

- `(company_id,occurred_at DESC)`;
- `(company_id,entity_type,entity_id,occurred_at)`;
- `(company_id,actor_user_id,occurred_at)`;
- `(request_id)`;
- `(correlation_id)` where not null.

## audit_partition_seals

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| period_from | timestamptz | NOT NULL |
| period_to | timestamptz | NOT NULL |
| row_count | bigint | NOT NULL |
| aggregate_hash | char(64) | NOT NULL |
| sealed_at | timestamptz | NOT NULL |
| storage_reference | text | NULL |

UNIQUE `(company_id,period_from,period_to)`.

CHECK period_to > period_from; row_count >=0.

Seal є defense-in-depth для виявлення несанкціонованої зміни audit history без global per-row hash serialization bottleneck.

---

# Outbox

## outbox_events

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| aggregate_type | varchar(80) | NOT NULL |
| aggregate_id | uuid | NOT NULL |
| event_type | varchar(120) | NOT NULL |
| payload | jsonb | NOT NULL |
| created_at | timestamptz | NOT NULL |
| published_at | timestamptz | NULL |
| attempt_count | integer | NOT NULL DEFAULT 0 |
| last_attempt_at | timestamptz | NULL |
| last_error | text | NULL |

CHECK attempt_count >=0.

Indexes:

- partial `(created_at)` WHERE published_at IS NULL;
- `(company_id,aggregate_type,aggregate_id,created_at)`.

Workers consume rows via `FOR UPDATE SKIP LOCKED` or equivalent. Outbox row вставляється в тій самій transaction, що business state change.

Retention published events визначається operations policy; purge не має видаляти canonical audit/business history.

---

# Reports

## report_exports

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| report_type | varchar(100) | NOT NULL |
| parameters | jsonb | NOT NULL DEFAULT `{}` |
| requested_by | uuid | NOT NULL |
| requested_at | timestamptz | NOT NULL |
| status | varchar(20) | NOT NULL |
| file_id | uuid | NULL |
| completed_at | timestamptz | NULL |
| error_code | varchar(100) | NULL |
| expires_at | timestamptz | NULL |

CHECK status IN (`QUEUED`,`RUNNING`,`READY`,`FAILED`,`EXPIRED`).

Indexes:

- `(company_id,requested_by,requested_at DESC)`;
- `(status,requested_at)` for worker queue if separate job system not used.

Report export є derived artifact; його retention може бути коротшим за source business data.

---

# Integrity Monitoring

## system_integrity_alerts

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| check_code | varchar(120) | NOT NULL |
| severity | varchar(20) | NOT NULL |
| entity_type | varchar(80) | NULL |
| entity_id | uuid | NULL |
| detected_at | timestamptz | NOT NULL |
| details | jsonb | NOT NULL DEFAULT `{}` |
| status | varchar(20) | NOT NULL |
| acknowledged_at | timestamptz | NULL |
| acknowledged_by | uuid | NULL |
| resolved_at | timestamptz | NULL |
| resolved_by | uuid | NULL |
| resolution_comment | text | NULL |

CHECK severity IN (`INFO`,`WARNING`,`ERROR`,`CRITICAL`).

CHECK status IN (`OPEN`,`ACKNOWLEDGED`,`RESOLVED`).

Indexes:

- `(company_id,status,severity,detected_at DESC)`;
- `(company_id,check_code,detected_at DESC)`;
- `(entity_type,entity_id)` where entity_id not null.

Integrity checker лише виявляє аномалію; він не silent-fix-ить production business history.

Приклади checks:

- `CLOSED_TRIP_WITHOUT_SNAPSHOT`;
- `AUTHORIZED_RELEASE_WITHOUT_AUTHORIZATION`;
- `WAYBILL_CURRENT_VERSION_MISMATCH`;
- `CLOSED_DUTY_WITH_OPEN_TRIP`;
- `ORPHAN_OBJECT_FILE_REFERENCE`;
- `VEHICLE_RUNTIME_PROJECTION_MISMATCH`;
- `OUTBOX_STUCK`.

---

# Optional job execution table

MVP може використати зовнішню job queue/Redis або DB-backed worker. Якщо обирається DB-backed job model, `background_jobs` має бути окремою технічною table і не змішуватися з `outbox_events`.

Outbox = гарантія інтеграційної події після business transaction. Job queue = механізм виконання роботи. Це різні concepts.

---

# Security logs

Authentication failures, session revocations та permission changes мають audit/security trace. Якщо volume auth logs значно перевищить business audit, architecture може додати окрему partitioned `security_events` table, але M0 не робить її обов'язковою.

---

# Derived read models

Для MVP reports/boards дозволені:

- SQL views;
- materialized views;
- rebuildable projection tables.

Derived read model не стає canonical source of truth. Будь-яка projection table повинна мати documented rebuild strategy.
