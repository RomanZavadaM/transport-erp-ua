# Транзакційні межі критичних API-команд

Статус: **architecture-v1.6 baseline**

Кожна critical command виконується як одна application transaction: або всі business effects commit-яться разом, або жоден.

## 0. Local authority + transfer-lock guard

Перед будь-якою business mutation local backend перевіряє дві окремі речі:

1. **Authority**:
   - `LOCAL` — local mutation може бути дозволена за звичайними permission/state rules;
   - `CENTRAL` — local mutation заборонена, повертається стабільна помилка на кшталт `409 RECORD_MANAGED_CENTRALLY`.
2. **Temporary transfer lock**:
   - якщо record включений у вже схвалений активний transfer batch, ordinary business mutation тимчасово блокується, щоб approved payload не змінився під час доставки.

`PENDING_APPROVAL`, `TRANSFERRING`, `FAILED` — це transfer-batch statuses, а не authority states. До verified central ACK authority залишається `LOCAL`.

UI лише відображає ці правила; гарантія знаходиться в backend.

## 1. Physical transaction profile

### Local SQLite

Критична write command використовує контрольовану SQLite write transaction. Для resource-conflict операцій backend перечитує актуальний стан усередині transaction перед INSERT/UPDATE.

### Central PostgreSQL

Ті самі application rules можуть додатково підсилюватися row locks, exclusion constraints, RLS та іншими PostgreSQL mechanisms.

Бізнес-правило не може залежати виключно від PostgreSQL feature, якщо воно потрібне local.

## 2. Assign vehicle to Duty

`POST /duties/{id}/assign-vehicle`

Transaction:

1. authority/transfer-lock guard;
2. load current Duty state;
3. verify vehicle lifecycle/context;
4. re-check overlapping assignment;
5. insert assignment;
6. update aggregate `row_version`;
7. append Duty event where used;
8. append audit;
9. commit.

Conflict → rollback → `409 VEHICLE_TIME_CONFLICT`.

Central PostgreSQL може додатково мати exclusion constraint.

## 3. Assign driver

Аналогічно vehicle assignment:

- authority/transfer-lock guard;
- current-state/permission validation;
- overlap check inside write transaction;
- insert assignment;
- event/audit;
- commit.

`crew_mode` зберігається явно і не виводиться автоматично з user role.

## 4. Replace vehicle / driver

Не переписуємо historical assignment.

Transaction:

- authority/transfer-lock guard;
- verify Duty state;
- validate `effective_at`;
- close/supersede previous active assignment/usage;
- create new assignment/usage;
- validate conflicts;
- event/audit;
- commit.

## 5. Complete qualified technical check

`POST /releases/{id}/technical-checks`

Transaction:

- authority/transfer-lock guard для local-owned Release/Duty context;
- permission/qualification validation;
- create completed check + details/results;
- derive final result server-side;
- create required blocking defect in same transaction where policy requires it;
- event/audit;
- commit.

Completed check immutable. Correction = invalidation + new check.

## 6. Complete medical check

`POST /releases/{id}/medical-checks`

Transaction:

- authority/transfer-lock guard;
- permission validation;
- create check/detail;
- derive `FIT`/`UNFIT`;
- audit;
- commit.

Completed record не редагується напряму.

## 7. Complete driver pre-departure check

Transaction:

1. authority/transfer-lock guard;
2. verify assigned driver/authorized exception;
3. verify vehicle/effective assignment;
4. create completed evidence;
5. derive result server-side;
6. audit/event;
7. commit.

Driver check не підміняє qualified technical check.

## 8. Evaluate Release

Transaction:

- authority/transfer-lock guard;
- read current assignments/checks/documents/defects/repairs;
- determine actual context;
- select applicable compliance rules;
- create new evaluation batch;
- persist rule results;
- derive `READY/BLOCKED` where applicable;
- audit/event;
- commit.

Old evaluation batch не UPDATE-иться.

## 9. Authorize Release

Transaction:

1. authority/transfer-lock guard;
2. verify optimistic version (`If-Match`/row version);
3. load latest Duty/Release/assignments;
4. fresh-evaluate all blocking rules;
5. persist evaluation evidence;
6. if any blocking FAIL → rollback/no authorization;
7. create positive authorization;
8. set Release/Duty authorized states;
9. event/audit;
10. commit.

Local SQLite не потребує PostgreSQL row-lock API; correctness забезпечує controlled local write transaction + current-state recheck. Central PostgreSQL може додатково lock rows.

## 10. Allocate Waybill number / create Waybill

Transaction:

1. authority/transfer-lock guard;
2. verify Duty/Waybill policy;
3. verify PRIMARY uniqueness where required;
4. atomically obtain next number from local/central number sequence;
5. create Waybill;
6. audit;
7. commit.

`MAX(number)+1` заборонено.

Для кількох autonomous local nodes numbering policy повинна мати series/prefix/range strategy, щоб local issuance не залежала від постійного central connection.

## 11. Generate Waybill version

Transaction:

- authority/transfer-lock guard;
- verify state/version;
- create immutable document snapshot/version metadata;
- audit;
- commit.

PDF generation може виконувати локальна background task, яку запускає сам desktop application. Окремий queue server не потрібен.

## 12. Duty depart

Transaction:

- authority/transfer-lock guard;
- verify Release authorization;
- validate odometer;
- append confirmed odometer reading;
- create/update actual usage;
- set Release `USED`;
- set Duty `ON_LINE`;
- event/audit;
- commit.

## 13. Duty return

Transaction:

- authority/transfer-lock guard;
- verify `ON_LINE`;
- validate arrival facts/odometer;
- close actual usage periods;
- set `RETURNED`;
- event/audit;
- commit.

## 14. Trip close

Transaction:

- authority/transfer-lock guard;
- verify `COMPLETED`;
- validate required facts;
- create immutable actual snapshot/version;
- set effective snapshot;
- set Trip `CLOSED`;
- event/audit;
- commit.

## 15. Duty close

Transaction:

- authority/transfer-lock guard;
- verify linked Trips CLOSED/CANCELLED as required;
- verify return facts/blocking exceptions;
- set `CLOSED`;
- audit/event;
- commit.

## 16. Waybill close

Transaction:

- authority/transfer-lock guard;
- verify closing guards;
- finalize immutable version reference;
- set `CLOSED`;
- audit;
- commit.

## 17. Closed history correction

Closed entity не reopen-иться звичайним edit.

Local correction дозволена лише поки authority=`LOCAL` і немає active transfer lock.

Після authority=`CENTRAL` correction створюється/застосовується на central; local отримує нову read-only effective version.

Correction створює new immutable snapshot/version, залишаючи попередню history.

## 18. Fuel correction

Historical fuel row не UPDATE-иться.

Correction = reversal/correction record + audit за затвердженою ledger-схемою.

Authority/transfer-lock guard діє так само, як для інших business data.

## 19. Prepare transfer batch

Створення pending batch **не передає дані і не змінює authority**.

Transaction:

1. select candidate records;
2. verify authority=`LOCAL`;
3. verify records are not already transfer-locked by another active approved batch;
4. include required dependencies;
5. snapshot versions/checksums;
6. create `transfer_batch` + `transfer_items` зі статусом `PENDING_APPROVAL`;
7. audit `TRANSFER_PREPARED`;
8. commit.

Rule або central request може виконати цей етап автоматично.

## 20. Local approve transfer

Фактичну передачу завжди підтверджує локальний оператор.

Transaction:

1. load pending batch;
2. verify item versions/checksums still match;
3. if changed → reject approval and rebuild batch;
4. set `approved_by/approved_at`;
5. set batch `TRANSFERRING`;
6. set temporary transfer lock on included records;
7. create delivery/outbox row;
8. audit `TRANSFER_APPROVED`;
9. commit.

Authority records залишається `LOCAL`.

## 21. Delivery retry

Network delivery is outside the business transaction but is idempotent by `origin_node_id + transfer_batch_id`.

On timeout/network error:

- batch стає retryable/`FAILED` згідно implementation;
- authority records залишається `LOCAL`;
- temporary transfer lock лишається під час retry, щоб payload не змінився;
- application може retry identical approved payload;
- оператор бачить status/error.

Якщо workflow дозволяє скасувати failed batch, cancellation transaction знімає transfer lock і лишає authority=`LOCAL`.

No Kafka/Redis is required for local retry.

## 22. Apply central ACK locally

Після verified central ACK:

Transaction:

1. load transfer batch;
2. verify receipt matches batch/node/checksum;
3. mark batch `ACKNOWLEDGED`;
4. set included records authority=`CENTRAL`;
5. clear temporary transfer lock;
6. persist `central_ack_id`/timestamp/version;
7. mark delivery complete;
8. audit `TRANSFER_ACKNOWLEDGED` and `LOCAL→CENTRAL` authority transition;
9. commit.

Only this transaction permanently removes local edit rights.

## 23. Receive batch on Central

Central receive is idempotent.

Transaction:

1. authenticate/identify origin node;
2. validate approved batch envelope/checksum;
3. check unique `origin_node_id + transfer_batch_id`;
4. if already accepted, return existing logical ACK;
5. otherwise persist business data/versions under central authority;
6. record central audit/receipt;
7. commit;
8. return ACK.

## 24. Central change returned to Local

Central may send a newer version/snapshot for a record authority=`CENTRAL`.

Local transaction:

- verify record authority=`CENTRAL`;
- verify monotonic central version/receipt;
- update local read-only representation through system sync path;
- audit;
- commit.

This does not restore local edit rights.

## 25. Audit rule

Critical audit entry is written in the same application transaction as the business state change whenever practical.

Transfer preparation, approval, ACK, cancellation, restore and authority changes are always audited.

## 26. Outbox rule

Architecture-v1.6 **does not append integration outbox events to every business mutation by default**.

Local transfer delivery outbox is created when the operator approves an actual transfer batch. Other async jobs use an outbox only when there is a concrete need.

## 27. Concurrency

### Local

SQLite has one coordinated application writer for critical writes. Keep transactions short; do not perform network calls while holding the write transaction.

### Central

PostgreSQL may use deterministic lock ordering and row locks for multi-aggregate operations.

## 28. Isolation

Local SQLite uses its transaction/locking model with application-side current-state checks.

Central PostgreSQL default remains `READ COMMITTED` plus explicit constraints/locks where required. `SERIALIZABLE` only after specific design/benchmark justification.
