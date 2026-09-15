# Спостережуваність системи

Статус: **M0 production baseline**

## 1. Ціль

Observability повинна дозволити відповісти на питання:

- система доступна чи ні;
- який компонент деградував;
- чи є втрата/затримка даних;
- чи працює backup;
- чи є черга невиконаних jobs/outbox events;
- чи виникли integrity problems;
- який release зараз працює;
- хто і коли виконав критичну дію.

## 2. Три рівні

### Logs

Structured JSON logs з:

- timestamp;
- level;
- service;
- environment;
- request_id;
- correlation_id;
- user_id там, де допустимо;
- company_id там, де допустимо;
- endpoint/command;
- duration_ms;
- result/error_code;
- release/version.

### Metrics

Мінімум:

- request rate;
- HTTP error rate;
- API latency percentiles;
- active DB connections;
- connection-pool saturation;
- DB transaction errors/deadlocks;
- worker queue depth;
- job age;
- outbox unpublished count/age;
- backup status;
- WAL archive lag;
- object replication lag;
- integrity alerts;
- disk/storage capacity;
- CPU/RAM;
- container restarts.

### Health / synthetic checks

Окремо:

- `/health/live` — process alive;
- `/health/ready` — required dependencies доступні;
- synthetic operational checks — ключові read-only paths і staging smoke flows.

## 3. Liveness

Liveness не повинен перевіряти всі зовнішні системи.

Його мета — відповісти, чи живий application process.

Невдала залежність не повинна автоматично створювати restart loop application container.

## 4. Readiness

Readiness перевіряє мінімум:

- PostgreSQL connection;
- schema/revision compatibility;
- critical configuration loaded;
- object storage reachable, якщо API path залежить від нього.

Redis не повинен робити весь API `not ready`, якщо Redis використовується лише для некритичного cache.

## 5. Security logging

Окремо логуються:

- failed login;
- account lock/throttle;
- permission denied для critical actions;
- session revoke;
- role/permission changes;
- credential/config rotation events;
- suspicious rate-limit triggers.

## 6. Заборонені дані у logs

Не записуються у звичайний application log:

- passwords;
- access/refresh tokens;
- session cookies;
- private keys;
- full authorization headers;
- backup credentials;
- medical details понад мінімально необхідний audit факт;
- document binary contents;
- full request payload, якщо він містить sensitive data.

Для debugging payload redaction є обов’язковим.

## 7. Audit ≠ application log

`audit_log` — business/security evidence і має окрему retention/immutability policy.

Application logs — operational diagnostics.

Не можна використовувати application log як єдиний audit trail.

## 8. Alert severity

### Critical

Приклади:

- production API unavailable;
- PostgreSQL unavailable;
- confirmed backup/restore failure beyond RPO window;
- WAL archiving stopped;
- storage nearly full with imminent write failure;
- integrity alert, який ставить під сумнів CLOSED history;
- credential compromise.

### High

- growing DB connection saturation;
- worker queue stalled;
- outbox age above threshold;
- object replication lag above target;
- repeated 5xx spike;
- backup delayed, але RPO ще не порушений.

### Warning

- storage approaching threshold;
- increasing latency;
- failed noncritical background job;
- expiring TLS certificate;
- restore drill due soon.

## 9. Alert deduplication

Monitoring не повинен надсилати сотні однакових alerts.

Потрібні:

- grouping;
- deduplication;
- silence/maintenance windows;
- escalation rules;
- recovery notification.

## 10. SLO indicators

До production launch вимірюємо щонайменше:

- API availability;
- p95/p99 latency ключових reads/commands;
- failed critical command rate;
- backup success ratio;
- restore drill success;
- outbox delivery delay;
- worker job delay.

Формальні SLA/SLO значення можуть бути затверджені бізнесом пізніше, але метрики мають збиратися від першої production версії.

## 11. Dashboard: Operations

Один operational dashboard повинен показувати:

- current release;
- application health;
- DB health;
- request rate/error rate/latency;
- worker status;
- outbox backlog;
- last successful DB backup;
- last successful WAL archive;
- last successful object backup/replication;
- last successful restore drill;
- open integrity alerts;
- storage capacity.

## 12. Database monitoring

Мінімум:

- active/idle connections;
- long-running transactions;
- locks;
- deadlocks;
- query latency;
- slow queries;
- replication/archive status where applicable;
- database size growth;
- table/index bloat trend where meaningful.

`pg_stat_statements` або еквівалентний PostgreSQL query statistics mechanism рекомендований для production profiling.

## 13. Worker / outbox monitoring

Окремо контролюємо:

- queued jobs;
- oldest queued job age;
- retry count;
- dead-letter/final-failed jobs;
- unpublished outbox events;
- oldest unpublished outbox event;
- repeated integration errors.

Не можна вважати систему healthy лише тому, що HTTP API відповідає 200, якщо critical worker queue стоїть годинами.

## 14. Backup observability

Dashboard/alerts мають знати:

- last backup start/end;
- backup size;
- verification result;
- WAL archive freshness;
- off-site repository reachability;
- last restore drill;
- measured restore duration;
- RPO/RTO target status.

## 15. Integrity alerts

`system_integrity_alerts` повинні мати окремий dashboard і escalation.

Особливо критичні:

- CLOSED trip без snapshot;
- CLOSED Waybill без current immutable version;
- Waybill version без PDF object;
- hash mismatch;
- authorized Release без authorization/evaluation evidence;
- cross-tenant anomaly;
- number-sequence inconsistency.

## 16. Release observability

Після deployment автоматично фіксується:

- Git SHA;
- release tag;
- image digest;
- migration revision;
- deployment timestamp;
- environment.

При incident оператор повинен за хвилини визначити, який exact build працює.

## 17. Retention

Operational logs зберігаються обмежений строк і ротуються.

Конкретний retention залежить від storage/security policy; baseline — не зберігати debug logs безстроково.

Audit/legal evidence має окрему retention policy і не підпадає під звичайну log rotation.

## 18. Час

Усі server logs/metrics timestamps зберігаються в UTC.

UI може показувати `Europe/Kyiv` або locale timezone, але кореляція incident timeline базується на UTC timestamps.

## 19. Production readiness

Перед production запуском перевіряється:

- health endpoints;
- dashboards;
- Critical/High alerts;
- backup alerts;
- disk/storage alerts;
- outbox/worker alerts;
- integrity alerts;
- release/version visibility;
- log redaction.

Система без перевірених alerts не вважається production-ready.
