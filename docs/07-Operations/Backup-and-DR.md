# Резервне копіювання та Disaster Recovery

Статус: **M0 production baseline**

## 1. Мета

Backup policy повинна гарантувати не факт існування архіву, а можливість відновити узгоджений стан:

- PostgreSQL;
- Waybill PDF та вкладення;
- configuration metadata;
- document templates;
- audit evidence;
- release/version information.

Backup не вважається працездатним, доки відновлення не було реально перевірене.

## 2. Цільові RPO / RTO для MVP

Початковий production baseline:

| Компонент | Target RPO | Target RTO |
|---|---:|---:|
| PostgreSQL transactional data | ≤ 15 хв | ≤ 4 год |
| object storage: PDF/attachments | ≤ 1 год | ≤ 4 год |
| application/configuration state | ≤ 24 год | ≤ 2 год |
| audit off-site seal/evidence | ≤ 24 год | ≤ 24 год |

RPO/RTO є операційними цілями, а не гарантією без перевірених restore drills.

Якщо бізнес-власник встановить жорсткіші вимоги, topology/backup schedule переглядається до production launch.

## 3. PostgreSQL backup strategy

Рекомендований механізм — backup system з підтримкою:

- physical base backup;
- continuous WAL archiving;
- point-in-time recovery;
- encryption;
- S3-compatible/off-site repository;
- backup integrity verification.

Конкретний інструмент може бути `pgBackRest`, `WAL-G` або еквівалент, але backup format не повинен бути саморобним application script.

### Baseline schedule

- continuous WAL archiving;
- full physical backup — щотижня;
- differential backup — щодня;
- backup verification — автоматично після створення;
- PITR window — щонайменше 14 днів;
- month-end immutable/off-site copy — 12 місяців як початковий operational baseline.

Це backup retention, а не legal retention business records.

## 4. WAL archive

WAL archive зберігається поза PostgreSQL host.

Вимоги:

- encrypted transport;
- encrypted at rest;
- автоматичний alert при archive failure/lag;
- контроль, що archive destination не заповнений;
- періодичний restore до random point-in-time.

Втрата WAL archiving більше допустимого RPO повинна створювати production alert високого пріоритету.

## 5. Off-site правило

Мінімум одна backup copy повинна знаходитися в окремому failure domain від production data node.

Не вважаються off-site backup:

- інший каталог того самого диска;
- інший Docker volume того самого host;
- архів на тому самому VPS;
- snapshot єдиного VPS як єдина backup strategy.

## 6. Object storage backup

Для PDF та вкладень:

- primary S3-compatible storage;
- bucket versioning;
- регулярна off-site replication/backup;
- object inventory;
- SHA-256 у PostgreSQL;
- контроль missing/orphaned objects;
- retention/object-lock після затвердження regulatory policy.

Ціль off-site replication для нових critical objects — не пізніше 1 години від створення.

Для фінальних Waybill PDF бажано копіювати object у backup destination асинхронно одразу після успішного запису primary object.

## 7. Узгодженість PostgreSQL ↔ Object Storage

DB backup і file backup не є повністю atomic між двома системами.

Тому integrity checker повинен знаходити:

- DB record → object відсутній;
- object → metadata record відсутній;
- SHA-256 mismatch;
- CLOSED Waybill без final PDF;
- `waybill_version` без доступного immutable object.

Під час DR допускається, що DB відновлена до точки, для якої деякі пізніші object versions вже існують. Такі objects не видаляються автоматично; вони класифікуються як orphan candidates для review.

## 8. Configuration та secrets backup

Backup configuration розділяється на:

### Versioned, non-secret

У Git:

- Compose templates;
- reverse-proxy config templates;
- migration code;
- environment variable names/examples;
- monitoring rules;
- runbooks.

### Secret material

Поза Git:

- production passwords;
- private keys;
- JWT/session signing material;
- object-storage credentials;
- backup repository credentials.

Secrets backup має бути encrypted і доступний лише обмеженому recovery role.

## 9. Restore environments

Відновлення ніколи вперше не тестується на production.

Має існувати temporary restore environment, у якому можна:

1. розгорнути clean PostgreSQL;
2. відновити base/differential backup;
3. replay WAL до потрібної точки;
4. підключити копію/restore object storage;
5. запустити schema/integrity checks;
6. виконати application smoke tests.

## 10. Restore drill cadence

Мінімальний baseline:

- автоматичний backup verification — кожен backup cycle;
- PostgreSQL restore drill — щомісяця;
- object restore sample — щомісяця;
- full disaster recovery exercise — щокварталу;
- обов'язковий full restore test перед першим production launch.

Restore drill має створювати evidence/report:

- дата;
- backup set;
- target point-in-time;
- фактичний restore duration;
- integrity results;
- smoke-test results;
- виявлені проблеми;
- відповідальний.

## 11. DR scenarios

### DR-01 — Application node lost

Очікування:

- PostgreSQL/object storage intact;
- підняти replacement application node;
- deploy pinned release images;
- restore configuration/secrets;
- connect to data services;
- readiness + smoke tests.

Ціль: RTO ≤ 2 години.

### DR-02 — Data node lost, off-site backups intact

1. provision replacement data node;
2. restore PostgreSQL latest valid backup;
3. replay WAL до вибраної point-in-time;
4. restore/connect object storage;
5. run integrity checker;
6. open system in maintenance/read-only mode for verification;
7. smoke tests;
8. reopen writes.

Ціль: RTO ≤ 4 години, DB RPO ≤ 15 хвилин.

### DR-03 — Accidental logical corruption

Приклади:

- faulty deployment;
- unintended bulk write;
- operator mistake.

Не відновлюємо production DB поверх себе одразу.

Спочатку:

1. stop/limit writes;
2. determine corruption time;
3. restore temporary DB to candidate PITR point;
4. validate business data;
5. choose recovery strategy: correction, selective recovery або full PITR cutover;
6. record incident/audit.

### DR-04 — Object storage corruption/deletion

1. disable destructive automation;
2. identify affected objects;
3. compare inventory/hash;
4. restore previous object versions/off-site copies;
5. run DB↔object integrity checker.

### DR-05 — Credential compromise

1. revoke/rotate compromised credentials;
2. invalidate sessions/tokens where required;
3. rotate dependent credentials;
4. inspect audit/security logs;
5. verify backup credentials separately;
6. preserve forensic evidence.

### DR-06 — Total site/provider loss

Recovery uses:

- Git/release metadata;
- off-site database backup + WAL;
- off-site object backup;
- encrypted recovery secrets;
- documented infrastructure/runbooks.

Production host snapshots alone не є достатніми.

## 12. Recovery modes

Система повинна підтримувати operationally:

- normal read/write;
- maintenance mode;
- read-only/recovery verification mode.

Після DR пишучий режим не вмикається до завершення мінімального integrity checklist.

## 13. Post-restore integrity checklist

Обов'язково перевірити:

- schema/Alembic revision;
- tenant counts;
- users/roles basic integrity;
- CLOSED trips with snapshots;
- Waybill/version/PDF availability;
- release authorizations;
- audit continuity;
- outbox state;
- object hashes/sample;
- number sequences;
- newest odometer readings;
- backup configuration itself.

## 14. Backup monitoring

Alerts:

- backup missed;
- backup failed;
- WAL archive delay;
- restore verification failed;
- repository capacity threshold;
- object replication lag;
- last successful restore drill expired.

Dashboard має показувати не тільки last backup, а також **last successful restore test**.

## 15. Відповідальність

До production launch мають бути визначені ролі:

- incident commander;
- infrastructure operator;
- database recovery operator;
- application verifier;
- business owner, який дозволяє відновлення write operations.

Одна людина може виконувати декілька ролей у невеликому підприємстві, але ролі мають бути явно визначені.

## 16. Правило production readiness

Production запуск заборонений, якщо:

- off-site backup не налаштований;
- WAL archiving не перевірений;
- object backup не перевірений;
- recovery secrets недоступні за documented procedure;
- не виконано full restore drill;
- measured restore time не вкладається в погоджений RTO без прийнятого risk exception.
