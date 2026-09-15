# Disaster Recovery Runbook

Статус: **M0 production baseline**

## 1. Мета

Цей runbook задає порядок прийняття рішень під час суттєвої production аварії. Низькорівневі інструкції конкретного backup tool зберігатимуться окремо після вибору infrastructure implementation.

## 2. Коли активується DR

DR process використовується, коли звичайний restart/redeploy не відновлює систему або існує ризик втрати/пошкодження даних.

Типові класи:

- втрата application node;
- втрата data node;
- logical data corruption;
- object-storage corruption/deletion;
- credential/security incident;
- повна втрата site/provider.

## 3. Перша фаза

Після оголошення incident:

1. призначити incident commander;
2. зафіксувати час виявлення;
3. обмежити write operations, якщо integrity під питанням;
4. зберегти logs та evidence;
5. зафіксувати current release і migration revision;
6. перевірити останній успішний backup/WAL/object-replication status;
7. вибрати recovery strategy.

## 4. Recovery strategies

- **Application rebuild** — data services не пошкоджені;
- **Point-in-time database recovery** — потрібне повернення до перевіреної точки;
- **Data-node rebuild** — production data node втрачено;
- **Controlled business correction** — проблема локальна і не потребує глобального rollback;
- **Site rebuild** — весь production environment відновлюється в іншому failure domain.

## 5. Candidate restore principle

Відновлена копія спочатку перевіряється як candidate environment, а не відразу оголошується production.

Перевіряються:

- schema/migration revision;
- обрана recovery point;
- основні entity counts;
- CLOSED Trip snapshots;
- Waybill/version/PDF history;
- Release authorization history;
- audit continuity;
- object availability/hash;
- integrity checker.

## 6. Maintenance / read-only mode

Після technical restore система спочатку запускається в maintenance або read-only verification mode.

Normal write mode не вмикається, поки:

- readiness checks не пройдені;
- critical smoke tests не пройдені;
- integrity gate не пройдений;
- business owner не погодив повернення operational writes.

## 7. Smoke checks

Мінімум перевіряються:

- authentication;
- читання Fleet/Drivers/Routes;
- Dispatcher Board;
- historical Duty/Trip;
- Release history;
- historical Waybill PDF;
- audit query;
- object download;
- number sequence sanity;
- worker/outbox health.

## 8. Integrity gate

Normal writes заборонені при unresolved CRITICAL alert щодо:

- tenant isolation;
- CLOSED history snapshots;
- Waybill version/PDF availability;
- audit integrity;
- document numbering;
- Release authorization evidence.

## 9. Ролі відновлення

Потрібні функціональні ролі:

- incident commander;
- infrastructure operator;
- database recovery operator;
- application verifier;
- business owner / operational approver.

У невеликому підприємстві одна людина може виконувати кілька ролей, але відповідальність має бути явно призначена.

## 10. Рішення про повернення в production

Перед normal operation фіксуються:

- recovery point;
- фактичний RPO;
- фактичний RTO;
- відомі втрачені transactions, якщо такі є;
- open risks;
- approvals.

## 11. Після incident

Обов'язково:

- посилений monitoring;
- новий перевірений backup cycle;
- перевірка off-site copy;
- incident report;
- root-cause analysis;
- corrective actions;
- оновлення runbook/tests;
- credential rotation, якщо incident пов'язаний із security.

## 12. Evidence

Incident evidence зберігає:

- timeline;
- alerts;
- major decisions/actions;
- backup/recovery set identifiers;
- recovery point;
- restored release/schema revision;
- smoke/integrity results;
- approvals;
- measured RPO/RTO;
- lessons learned.

## 13. Exercises

- restore drill — щомісяця;
- object restore sample — щомісяця;
- DR exercise — щокварталу;
- full restore test — обов'язково перед першим production launch.

Runbook вважається перевіреним тільки після практичного exercise, а не після review документа.
