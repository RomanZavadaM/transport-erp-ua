# Транзакційні межі критичних API-команд

Статус: **M0 draft**

Кожна critical command виконується як одна application transaction. Або всі її business effects commit-яться разом, або жоден.

## 1. Assign vehicle to Duty

`POST /duties/{id}/assign-vehicle`

Одна transaction:

1. load/lock Duty;
2. verify current state;
3. verify vehicle tenant/lifecycle;
4. insert assignment;
5. PostgreSQL EXCLUDE перевіряє overlap;
6. update aggregate version;
7. append Duty event;
8. append audit;
9. append outbox event;
10. commit.

Constraint violation → rollback → `409 VEHICLE_TIME_CONFLICT`.

## 2. Assign driver

Аналогічна transaction з DB exclusion для driver/time.

## 3. Replace vehicle / driver

Не UPDATE старого historical assignment.

Transaction:

- lock Duty;
- validate effective_at;
- close/supersede попередній active assignment/usage відповідно до workflow;
- create new assignment/usage;
- validate conflicts;
- append operational event;
- audit;
- outbox;
- commit.

## 4. Complete technical check

Transaction:

- lock Release/subject as needed;
- create completed check + detail + checklist results;
- derive final result server-side;
- якщо blocking failure → create blocking defect у тій самій transaction;
- event/audit;
- commit.

Не допускається `FAILED check` без створеного required defect через partial failure.

## 5. Complete medical check

Transaction:

- validate actor/permission;
- create check/detail;
- mark completed result;
- audit;
- commit.

Completed record immutable. Invalidation є окремою command/transaction.

## 6. Evaluate Release

`POST /releases/{id}/evaluate`

Transaction:

- read current assignments/checks/documents/defects/repairs;
- create new `evaluation_batch_id`;
- insert rule results;
- derive evaluated release state (`READY/BLOCKED` where applicable);
- audit/event;
- commit.

Старі evaluation batches не UPDATE-яться.

## 7. Authorize Release

`POST /releases/{id}/authorize`

Одна з найкритичніших transaction:

1. lock Release;
2. lock Duty;
3. verify `If-Match`;
4. load effective assignments;
5. **fresh evaluate** all blocking rules;
6. persist evaluation batch;
7. якщо FAIL → no authorization;
8. ensure Waybill policy/preconditions;
9. create unique positive authorization;
10. set Release `AUTHORIZED`;
11. set Duty `AUTHORIZED`;
12. event;
13. audit;
14. outbox;
15. commit.

Жоден state не переходить в authorized до успішного завершення всіх guards.

## 8. Allocate Waybill number

Одна transaction:

1. lock `number_sequences` row;
2. take `next_value`;
3. increment sequence;
4. construct business number;
5. create Waybill;
6. DB UNIQUE confirms uniqueness;
7. audit;
8. commit.

`MAX(number)+1` заборонено.

Виданий/зарезервований business number не використовується повторно після business cancellation.

## 9. Generate Waybill version

Business snapshot/version creation і job identity повинні бути consistent.

Recommended transaction:

- lock Waybill;
- verify state/version;
- create immutable snapshot/version metadata in pending-generation state or enqueue stable job via outbox;
- audit/outbox;
- commit.

Worker генерує PDF idempotently для конкретного version ID. Він не створює нову business version самостійно.

## 10. Duty depart

Transaction:

- lock Duty + Release;
- verify AUTHORIZED/USED preconditions;
- verify authorization still applicable;
- validate odometer;
- append confirmed odometer reading;
- create actual vehicle/driver usage if needed;
- set Release `USED`;
- set Duty `ON_LINE`;
- event/audit/outbox;
- commit.

## 11. Duty return

Transaction:

- lock Duty;
- verify `ON_LINE`;
- validate arrival odometer >= departure;
- record return facts;
- close actual usage periods as appropriate;
- set `RETURNED`;
- event/audit/outbox;
- commit.

## 12. Trip close

Transaction:

- lock Trip;
- verify `COMPLETED`;
- validate required actual facts;
- create immutable `trip_actual_snapshot` new version;
- set effective snapshot ID;
- set Trip `CLOSED`;
- event/audit/outbox;
- commit.

Після commit historical snapshot не UPDATE-иться.

## 13. Duty close

Transaction:

- lock Duty;
- lock linked Trips у deterministic order;
- verify all required Trips CLOSED/CANCELLED;
- verify required return facts;
- verify no unresolved blocking exception;
- set `CLOSED`;
- audit/event/outbox;
- commit.

## 14. Waybill close

Transaction:

- lock Waybill/Duty;
- verify closing guards;
- create/finalize immutable document version reference;
- set Waybill `CLOSED`;
- audit/outbox;
- commit.

PDF generation may be asynchronous, але final close semantics повинні гарантувати, що canonical final version однозначно визначена.

## 15. Closed history correction

Correction не reopen-ить entity.

Transaction створення correction case:

- verify entity CLOSED;
- create `correction_case`;
- record reason/requester;
- audit;
- commit.

Transaction застосування approved correction:

- lock correction + entity;
- create new immutable snapshot/version;
- link previous version;
- switch effective version pointer;
- mark correction COMPLETED;
- audit/outbox;
- commit.

Старий snapshot/version залишається.

## 16. Fuel correction

Historical fuel operation не UPDATE-иться.

Correction transaction створює reversal + new correct operation або іншу затверджену ledger-схему, зв'язану з original record.

## 17. Outbox rule

Якщо business state змінився і зовнішня/async реакція важлива, outbox row вставляється **в тій самій DB transaction**.

Не допускається:

`commit business state → потім окремо спробувати записати event`.

## 18. Audit rule

Critical audit entry є частиною тієї самої transaction, якщо це не суперечить спеціальному security logging design.

## 19. Lock ordering

Canonical lock order для operations, де потрібні кілька aggregate/resource rows:

`Duty → Trips(sorted) → Vehicle/Driver resource state → Release → Waybill → Number Sequence`.

Будь-яке відхилення має пройти concurrency review.

## 20. Isolation

Default PostgreSQL isolation: `READ COMMITTED` + explicit row locks/constraints.

`SERIALIZABLE` використовується точково лише для operation, де це обґрунтовано окремим design review.