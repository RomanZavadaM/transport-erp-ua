# System Integrity Checker

Статус: **architecture-v1.6 baseline**

## 1. Призначення
Integrity Checker шукає стани, які не повинні виникати за нормальної роботи application rules, SQLite/PostgreSQL constraints та transfer flow.

Він не ремонтує business history автоматично.

## 2. Local Desktop — пріоритетні checks

На першому етапі перевіряємо те, що реально може зламати локальну роботу:

### SQLite / storage

- `SQLITE_INTEGRITY_FAILURE`;
- schema version не відповідає application version;
- DB/file directory недоступний;
- критично мало місця на диску;
- backup overdue/invalid manifest;
- document metadata посилається на відсутній local file;
- file checksum mismatch для immutable documents.

### Transfer / authority

- `TRANSFERRING_BATCH_WITHOUT_APPROVAL`;
- `ACKNOWLEDGED_BATCH_WITH_LOCAL_ITEMS`;
- `CENTRAL_RECORD_MUTATED_LOCALLY`;
- approved batch payload/version changed after approval;
- transfer checksum mismatch;
- duplicate/contradictory central receipt;
- central version lower than already stored local central version;
- stuck approved transfer above configured threshold.

### Business history

- CLOSED Trip без effective immutable snapshot;
- CLOSED Waybill без current final version;
- completed check, який був змінений поза correction/invalidation workflow;
- duplicate active vehicle/driver overlap;
- inconsistent odometer sequence;
- duplicate business document number там, де numbering policy забороняє дубль.

## 3. Central checks

Central додає:

- invalid origin node / transfer batch receipt;
- duplicate receive з різним checksum;
- company/context mismatch;
- PostgreSQL-specific constraint/integrity problems;
- missing central documents/storage objects;
- central backup/WAL issues, якщо відповідний механізм використовується.

Cross-company/RLS checks є central-specific і не нав’язуються Local Desktop.

## 4. Коли запускати Local checks

Не потрібен окремий scheduler cluster.

Практичний baseline:

- quick checks при startup;
- quick checks після application/schema update;
- transfer-related checks перед/після передачі;
- backup-related checks після backup/restore;
- full local consistency check вручну з екрана `Стан системи`;
- optional scheduled full check, якщо підприємству це потрібно.

Не запускаємо важкий scan кожні 15 хвилин без потреби.

## 5. Результат

Виявлена проблема зберігається у `system_integrity_alerts` або еквівалентному local registry:

- check code;
- severity;
- entity/batch id;
- detected_at;
- коротке пояснення;
- technical details;
- status;
- resolution information.

UI показує проблему зрозумілою мовою.

## 6. Severity

### CRITICAL

Ризик втрати/підміни даних або неможливість безпечно продовжувати writes.

Приклади: SQLite integrity failure, acknowledged transfer з суперечливим payload, broken immutable closed history.

### HIGH

Проблема, що заважає передачі, випуску, Waybill або backup.

### WARNING

Проблема, яку потрібно перевірити, але вона не доводить corruption.

## 7. Resolution

Resolution фіксує:

- хто перевірив;
- що сталося;
- що зроблено;
- коли закрито.

CLOSED history виправляється correction workflow, а не direct SQL UPDATE.

## 8. Auto-remediation

Автоматично можна:

- rebuild cache/read projection;
- retry identical approved transfer;
- refresh derived status.

Не можна auto-repair:

- Waybill historical versions;
- Trip snapshots;
- audit;
- completed checks;
- fuel history;
- transfer receipts/authority history шляхом silent rewrite.

## 9. Restore integration

Після Local restore перевірити мінімум:

- SQLite integrity;
- schema version;
- node id;
- transfer batches/receipts;
- authority state consistency;
- critical document files;
- audit availability.

Після Central restore додатково перевіряється PostgreSQL/storage/received batches.

## 10. Testability

Кожний critical check має automated fixture/test, який навмисно створює проблему й доводить, що checker її знаходить.

Checker не повинен перетворюватися на набір production-only ad-hoc SQL.

## 11. UI

Local desktop має дати оператору/адміністратору:

- `Перевірити систему`;
- список проблем;
- severity;
- зрозумілий опис;
- технічні деталі для підтримки;
- export diagnostic report.

Користувач не повинен запускати SQL-скрипти вручну для звичайної перевірки системи.
