# Audit, Transfer Queue, Reports & Integrity — architecture-v1.6

Цей документ описує логічну модель, спільну для local SQLite та central PostgreSQL. PostgreSQL-specific оптимізації не є вимогою локального вузла.

# 1. Audit

## audit_log

Append-only журнал важливих дій.

Мінімальні поля:

| Поле | Призначення |
|---|---|
| id | UUID/unique id |
| occurred_at | час події |
| actor_user_id | хто виконав дію, nullable для system action |
| action | стабільний код дії |
| entity_type | тип сутності |
| entity_id | id сутності |
| request_id | кореляція локальної команди/API |
| source | `LOCAL_APP`, `CENTRAL`, `SYSTEM`, інше контрольоване значення |
| reason | причина, де потрібна |
| before_data | optional serialized previous state |
| after_data | optional serialized new state |
| changed_fields | optional serialized field list |
| metadata | додатковий контекст без секретів |

Правила:

- normal application flow не UPDATE/DELETE audit rows;
- sensitive values маскуються до запису;
- local audit працює в SQLite без partitioning;
- central PostgreSQL може додати partitioning/indexes після підтвердженої потреби;
- audit transfer preparation/approval/ACK/authority change є обов’язковим.

# 2. Transfer batches

## transfer_batches

Оператор працює з пакетом передачі, а не з технічними outbox rows.

| Поле | Призначення |
|---|---|
| id | batch UUID |
| origin_node_id | локальний node UUID |
| status | `PENDING_APPROVAL`, `TRANSFERRING`, `FAILED`, `ACKNOWLEDGED`, `CANCELLED` |
| prepared_reason | `MANUAL`, `CENTRAL_REQUEST`, `RULE` |
| prepared_at | коли сформовано |
| prepared_by | хто сформував, nullable для rule/request |
| approved_by | локальний оператор, який підтвердив |
| approved_at | час підтвердження |
| started_at | початок передачі |
| acknowledged_at | час central ACK |
| central_ack_id | receipt центрального рівня |
| last_error | остання технічна помилка |
| retry_count | кількість повторів доставки |

Правила:

- без `approved_by/approved_at` batch не може перейти у `TRANSFERRING`;
- central request або rule не заповнюють approval автоматично;
- `ACKNOWLEDGED` ставиться лише після перевіреного central receipt;
- failed delivery не змінює authority даних;
- retry дозволений для того самого approved payload;
- зміна складу/payload після approval вимагає нового approval.

## transfer_items

| Поле | Призначення |
|---|---|
| transfer_batch_id | batch |
| entity_type | тип aggregate/root entity |
| entity_id | UUID |
| entity_version | version на момент approval |
| checksum | контроль approved payload |
| transfer_order | deterministic order за потреби |

PK/UNIQUE гарантує, що один item не дублюється в одному batch.

# 3. Business authority

Authority і transfer workflow — різні речі.

Для transferable aggregate/root зберігається:

- `authority = LOCAL | CENTRAL`;
- optional `transfer_lock_batch_id` для тимчасового блокування approved payload;
- `central_version` / `central_ack_id` / `central_synced_at` після переходу на central.

Правила:

- до valid ACK authority = `LOCAL`;
- `PENDING_APPROVAL`, `TRANSFERRING`, `FAILED` є статусами batch, не authority;
- після operator approval records можуть мати temporary transfer lock;
- failed/cancelled transfer не переводить authority у `CENTRAL`;
- після verified ACK local transaction встановлює authority=`CENTRAL` і прибирає temporary transfer lock;
- local backend відхиляє business UPDATE/DELETE для authority=`CENTRAL`.

UI лише відображає цю заборону; гарантія знаходиться в backend і за можливості підсилюється SQLite trigger.

# 4. Delivery outbox

## transfer_delivery_queue

Outbox — технічна черга надійної доставки **вже схваленого** batch.

| Поле | Призначення |
|---|---|
| id | delivery id |
| transfer_batch_id | batch |
| created_at | створено |
| available_at | коли можна повторити |
| attempt_count | кількість спроб |
| last_attempt_at | остання спроба |
| last_error | технічна помилка |
| completed_at | ACK оброблено |

Local SQLite має одного application-managed delivery worker. Немає потреби в `FOR UPDATE SKIP LOCKED`, Redis або queue broker.

Central PostgreSQL при масштабуванні може мати кілька workers.

# 5. Central receive receipt

Central endpoint приймає batch idempotently.

Central зберігає щонайменше:

- `origin_node_id`;
- `transfer_batch_id` UNIQUE;
- payload/checksum/version metadata;
- received_at;
- ack_id.

Повторне надсилання того самого незміненого batch повертає той самий логічний ACK і не дублює business rows.

# 6. Central changes back to local

Після authority=`CENTRAL` local copy є read-only.

Якщо central змінює запис, local може отримати нову version/snapshot. Це оновлення не повертає local edit rights.

# 7. Reports

Local reports можуть будуватися безпосередньо з SQLite.

Central reports можуть будуватися з PostgreSQL.

`report_exports`/background report queue вводиться лише коли реальний report потребує async generation.

# 8. Integrity Monitoring

Початкові local checks:

- `CENTRAL_RECORD_EDIT_ATTEMPT`;
- `ACKNOWLEDGED_BATCH_WITH_NONCENTRAL_ITEMS`;
- `TRANSFERRING_BATCH_WITHOUT_APPROVAL`;
- `TRANSFER_CHECKSUM_MISMATCH`;
- `TRANSFER_LOCK_WITHOUT_ACTIVE_BATCH`;
- `MISSING_LOCAL_DOCUMENT_FILE`;
- `SQLITE_INTEGRITY_FAILURE`;
- `BACKUP_OVERDUE`;
- `DISK_SPACE_LOW`.

Checker не silent-fix-ить business history.

# 9. Security logs

Failed login, role/permission changes, restore, backup, transfer approval та authority transition мають audit trace.

Окрема high-volume security table не потрібна до появи реальної потреби.

# 10. Що свідомо не робимо в M1.5

- audit partitioning на local;
- audit sealing infrastructure;
- Kafka/RabbitMQ;
- Redis queue;
- multi-worker local processing;
- event sourcing;
- multi-master conflict resolution;
- складні projection pipelines.

M1.5 повинен пройти сценарій:

`local edit → prepare batch → operator approve → temporary transfer lock → retry if needed → central ACK → authority LOCAL→CENTRAL → local read-only`.
