# Транзакційні межі критичних API-команд

Статус: **M0 freeze candidate**

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

Assignment/usage segment окремо зберігає `crew_mode`; внутрішній driver role не визначає regulatory crew mode автоматично.

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

## 4. Complete qualified technical check

`POST /releases/{id}/technical-checks`

Transaction:

- validate `technical_check.perform` та actor policy;
- lock Release/subject as needed;
- create completed check + detail + checklist results;
- derive final result server-side;
- якщо blocking failure потребує defect evidence → create blocking defect у тій самій transaction;
- event/audit;
- commit.

Не допускається `FAILED check`, для якого required blocking defect мав бути створений, без відповідного defect через partial failure.

Назва job role виконавця не є DB invariant; authorization визначається permission/qualification policy.

## 5. Complete medical check

`POST /releases/{id}/medical-checks`

Transaction:

- validate actor/permission;
- create check/detail;
- result тільки `FIT` або `UNFIT`;
- mark completed result;
- audit;
- commit.

Completed record immutable. Invalidation є окремою command/transaction.

## 6. Complete driver pre-departure technical check

`POST /releases/{id}/driver-predeparture-checks`

Transaction:

1. lock/read Release + Duty context;
2. verify caller має `driver_predeparture_check.perform`;
3. verify caller/subject відповідає assigned-driver scope або explicit authorized exception;
4. verify vehicle/effective assignment;
5. create `pre_trip_check` із `check_type=DRIVER_TECHNICAL_PREDEPARTURE`;
6. create versioned checklist results;
7. derive `PASSED/FAILED` server-side;
8. audit/event;
9. commit.

Completed check не редагується. Помилка → invalidation + new check.

Цей check не підмінює qualified `TECHNICAL` check; Release policy може вимагати обидва.

## 7. Evaluate Release

`POST /releases/{id}/evaluate`

Transaction:

- read current assignments/checks/documents/defects/repairs;
- determine current transport/service/route context;
- select applicable compliance rule versions by effective period/context;
- create new `evaluation_batch_id`;
- insert rule results;
- derive evaluated release state (`READY/BLOCKED` where applicable);
- audit/event;
- commit.

Старі evaluation batches не UPDATE-яться.

## 8. Authorize Release

`POST /releases/{id}/authorize`

Одна з найкритичніших transaction:

1. lock Release;
2. lock Duty;
3. verify `If-Match`;
4. load effective vehicle/driver assignments and actual policy context;
5. select applicable current rule versions;
6. **fresh evaluate** all blocking rules, включно з:
   - effective medical `FIT`;
   - qualified technical check;
   - driver pre-departure technical evidence;
   - contextual driver/vehicle/carrier/route documents/evidence;
   - blocking defects/repairs;
   - assignment/resource conflicts;
7. persist evaluation batch;
8. якщо blocking FAIL → no authorization;
9. ensure Waybill policy/preconditions where applicable;
10. create unique positive authorization;
11. set Release `AUTHORIZED`;
12. set Duty `AUTHORIZED`;
13. event;
14. audit;
15. outbox;
16. commit.

Жоден state не переходить в authorized до успішного завершення всіх guards.

## 9. Allocate Waybill number / create Waybill

Одна transaction:

1. lock Duty/Waybill policy context;
2. validate requested/default `document_role`;
3. for `PRIMARY`, verify no active non-cancelled PRIMARY Waybill exists;
4. lock applicable `number_sequences` row;
5. take `next_value`;
6. increment sequence;
7. construct business number;
8. create Waybill;
9. DB UNIQUE confirms number/PRIMARY-policy uniqueness;
10. audit;
11. commit.

`MAX(number)+1` заборонено.

Виданий/зарезервований business number не використовується повторно після business cancellation. Формат/reset sequence є enterprise policy.

## 10. Generate Waybill version

Business snapshot/version creation і job identity повинні бути consistent.

Recommended transaction:

- lock Waybill;
- verify state/version;
- create immutable snapshot/version metadata in pending-generation state or enqueue stable job via outbox;
- audit/outbox;
- commit.

Worker генерує PDF idempotently для конкретного version ID. Він не створює нову business version самостійно.

## 11. Duty depart

Transaction:

- lock Duty + Release;
- verify AUTHORIZED/USED preconditions;
- verify authorization still applicable;
- validate odometer;
- append confirmed odometer reading;
- create actual vehicle/driver usage if needed;
- preserve crew_mode on driver usage segments;
- set Release `USED`;
- set Duty `ON_LINE`;
- event/audit/outbox;
- commit.

## 12. Duty return

Transaction:

- lock Duty;
- verify `ON_LINE`;
- validate arrival odometer >= departure;
- record return facts;
- close actual usage periods as appropriate;
- set `RETURNED`;
- event/audit/outbox;
- commit.

## 13. Trip close

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

## 14. Duty close

Transaction:

- lock Duty;
- lock linked Trips у deterministic order;
- verify all required Trips CLOSED/CANCELLED;
- verify required return facts;
- verify no unresolved blocking exception;
- set `CLOSED`;
- audit/event/outbox;
- commit.

## 15. Waybill close

Transaction:

- lock Waybill/Duty;
- verify closing guards;
- create/finalize immutable document version reference;
- set Waybill `CLOSED`;
- audit/outbox;
- commit.

PDF generation may be asynchronous, але final close semantics повинні гарантувати, що canonical final version однозначно визначена.

## 16. Closed history correction

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

## 17. Fuel correction

Historical fuel operation не UPDATE-иться.

Correction transaction створює reversal + new correct operation або іншу затверджену ledger-схему, зв'язану з original record.

## 18. Outbox rule

Якщо business state змінився і зовнішня/async реакція важлива, outbox row вставляється **в тій самій DB transaction**.

Не допускається:

`commit business state → потім окремо спробувати записати event`.

## 19. Audit rule

Critical audit entry є частиною тієї самої transaction, якщо це не суперечить спеціальному security logging design.

## 20. Lock ordering

Canonical lock order для operations, де потрібні кілька aggregate/resource rows:

`Duty → Trips(sorted) → Vehicle/Driver resource state → Release → Waybill → Number Sequence`.

Будь-яке відхилення має пройти concurrency review.

## 21. Isolation

Default PostgreSQL isolation: `READ COMMITTED` + explicit row locks/constraints.

`SERIALIZABLE` використовується точково лише для operation, де це обґрунтовано окремим design review.
