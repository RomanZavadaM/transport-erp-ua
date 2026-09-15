# System Integrity Checker

Статус: **M0 production baseline**

## 1. Призначення

Integrity Checker — окремий контрольний механізм, який шукає логічно неможливі або підозрілі стани, що не повинні виникати за нормальної роботи application/business constraints.

Він **не ремонтує історичні дані автоматично**.

## 2. Джерело результатів

Виявлені проблеми записуються у `system_integrity_alerts` із:

- `check_code`;
- severity;
- entity type/id;
- detected_at;
- diagnostic details;
- status `OPEN/ACKNOWLEDGED/RESOLVED`.

## 3. Категорії checks

### Historical integrity

- CLOSED Trip без effective immutable actual snapshot;
- effective snapshot належить іншому Trip;
- CLOSED Waybill без current version;
- current Waybill version належить іншому Waybill;
- immutable version із відсутнім PDF object;
- snapshot/PDF SHA-256 mismatch;
- completed check, що був змінений поза invalidation workflow.

### Release integrity

- AUTHORIZED/USED Release без positive authorization;
- authorization без required evaluation batch;
- USED Release без фактичного Duty departure;
- release references inconsistent with Duty tenant.

### Assignment integrity

- overlapping active vehicle assignments, якщо DB constraint відсутній/пошкоджений;
- overlapping active driver assignments;
- один Trip у двох active Duty memberships;
- actual usage без відповідного Duty.

### Tenant integrity

- child `company_id` не відповідає parent company;
- cross-tenant reference, яку не повинно бути можливо створити;
- user role from another company без explicit system-role semantics.

### Documents/files

- metadata → object missing;
- object hash mismatch;
- required final PDF unavailable;
- orphan objects старші configured grace period;
- invalid template/version reference.

### Numbering

- duplicate business document number;
- `number_sequences.next_value` нижче вже використаного номера;
- reused cancelled/void document number там, де reuse заборонений.

### Odometer

- confirmed odometer sequence decreases без correction evidence;
- runtime projection differs from latest confirmed reading;
- Trip/Duty distance incompatible with stored readings beyond configured diagnostic tolerance.

### Audit/outbox

- critical business command without expected audit event;
- outbox record stuck above threshold;
- audit partition seal mismatch;
- unsealed period older than allowed threshold.

## 4. Severity

### CRITICAL

Потенційна втрата/підміна closed history або cross-tenant breach.

### HIGH

Operational inconsistency, що може вплинути на release/Waybill/reporting.

### WARNING

Діагностична розбіжність, яка не доводить corruption, але потребує review.

## 5. Schedule

Baseline:

- light checks — кожні 15 хв;
- medium checks — щогодини;
- full consistency scan — щоночі;
- post-restore full scan — обов'язково;
- post-major-migration scan — обов'язково.

Конкретні jobs можуть бути розділені за вартістю query.

## 6. Idempotency

Повторний detection тієї самої unresolved проблеми не створює нескінченні дублікати alerts.

Використовується deterministic issue key на основі:

- `check_code`;
- company;
- entity;
- relevant violation fingerprint.

## 7. Resolution

Integrity alert не вважається вирішеним лише через те, що його приховали.

Resolution має містити:

- хто перевірив;
- root cause;
- спосіб виправлення;
- correction/incident reference;
- resolved_at.

Якщо виправлення стосується CLOSED history, воно проходить через correction workflow, а не direct UPDATE.

## 8. Auto-remediation

Автоматично дозволено ремонтувати лише rebuildable projections/cache.

Наприклад:

- `vehicle_runtime_state` можна rebuild;
- materialized/report projection можна refresh.

Не можна auto-repair:

- Waybill versions;
- Trip snapshots;
- audit;
- completed checks;
- fuel ledger history;
- release decisions.

## 9. Monitoring

CRITICAL/HIGH alerts інтегруються з production monitoring.

Dashboard показує:

- open alerts by severity;
- oldest alert age;
- newly detected alerts;
- recurring checks;
- last successful full scan.

## 10. DR integration

Після restore/cutover система не переходить у normal write mode до завершення minimal integrity set:

- migrations/schema revision;
- tenant FK consistency;
- closed Trip snapshots;
- Waybill/PDF availability;
- Release authorization integrity;
- object hashes sample/full critical set;
- number sequence sanity;
- audit/outbox sanity.

## 11. Testability

Кожний check має fixture/test, який навмисно створює detectable inconsistency у test DB і доводить, що checker її знаходить.

Production checker не повинен бути набором ad-hoc SQL без automated tests.
