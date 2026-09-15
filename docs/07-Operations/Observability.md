# Спостережуваність системи

Статус: **architecture-v1.6 baseline**

## 1. Принцип
Observability має допомагати експлуатувати систему, а не створювати окремий інфраструктурний проєкт.

Local Desktop і Central мають різні потреби.

## 2. Local Desktop — що реально потрібно

У застосунку має бути простий екран **«Стан системи»**, де видно:

- версію TransportERP-UA;
- schema version;
- стан SQLite;
- розмір БД;
- вільне місце на диску;
- останній успішний backup;
- куди робиться backup;
- останню перевірку restore/integrity;
- кількість pending/failed transfer batches;
- останню помилку передачі;
- central connection status, якщо central налаштований;
- node id.

Цього достатньо для малого АТП без Prometheus/Grafana.

## 3. Local logs

Local application веде rotating logs у application-data каталозі.

Мінімальні поля:

- timestamp;
- level;
- application version;
- request/operation id;
- user id, де доречно;
- command/action;
- result/error code;
- transfer batch id, якщо стосується передачі.

Logs не повинні містити passwords, session secrets, private keys, повні sensitive payloads або медичні деталі понад необхідне.

Користувач/адміністратор має мати кнопку **«Відкрити журнал»** або **«Створити діагностичний пакет»**.

## 4. Local health checks

Local застосунок перевіряє щонайменше:

- SQLite відкривається;
- schema version підтримується поточною версією програми;
- application data directory доступний для запису;
- document directory доступний;
- backup destination доступний, якщо налаштований;
- вільного дискового місця достатньо;
- transfer queue не має застряглих approved batches понад configured threshold.

Несправність central не робить local application `unhealthy` для локальної роботи.

## 5. Local alerts

Не потрібна складна alert platform.

Застосунок показує оператору зрозумілі повідомлення:

- резервної копії давно не було;
- backup destination недоступний;
- мало місця на диску;
- SQLite integrity check failed;
- передача не завершилася;
- central запитує дані, що очікують локального підтвердження;
- local update/recovery required.

Critical повідомлення не повинні губитися після закриття toast — вони залишаються у системному стані до вирішення/підтвердження.

## 6. Audit ≠ log

Audit — business/security evidence.

Log — технічна діагностика.

Failed transfer може бути в log; approval/ACK/authority change обов’язково є і в audit.

## 7. Local transfer monitoring

UI показує окремо:

- `PENDING_APPROVAL`;
- `TRANSFERRING`;
- failed/retryable;
- `ACKNOWLEDGED`.

Оператор повинен бачити, **що саме чекає його підтвердження**, а не технічну “queue depth”.

Для failed batch показуються:

- час останньої спроби;
- коротка зрозуміла причина;
- кнопка retry/diagnostics, якщо доречно.

## 8. Local backup monitoring

Екран стану показує:

- останній backup;
- результат;
- розмір;
- destination;
- warning, якщо backup overdue;
- last restore/integrity verification.

Для малого АТП це важливіше за p99 latency dashboard.

## 9. Local release diagnostics

У UI завжди доступні:

- application version;
- build/Git SHA або release id;
- DB schema version;
- node id.

Це достатньо, щоб під час підтримки зрозуміти, яка версія реально встановлена.

## 10. Central observability

Central server має server-grade monitoring відповідно до масштабу.

Мінімально корисні показники:

- API availability/error rate;
- PostgreSQL health/connections;
- receive/ACK failures;
- pending central processing;
- backup status;
- disk/storage;
- open integrity alerts;
- current release/schema version.

При реальній потребі додаються Prometheus/Grafana або інший monitoring stack.

## 11. Central database monitoring

Для PostgreSQL доречні:

- long-running transactions;
- locks/deadlocks;
- slow queries;
- database growth;
- backup/WAL state, якщо WAL використовується;
- `pg_stat_statements` для profiling.

Це не local desktop requirement.

## 12. Health endpoints

Central API може мати:

- `/health/live`;
- `/health/ready`.

Local desktop може мати внутрішній health endpoint для desktop shell, але користувач не повинен працювати з ним вручну.

## 13. Sensitive data

Ні local, ні central logs не записують:

- passwords;
- session cookies/tokens;
- authorization headers;
- private keys;
- backup credentials;
- повні binary documents;
- sensitive payloads без redaction.

## 14. Production readiness Local Desktop

Перевірити:

- status screen;
- log rotation;
- diagnostic package;
- backup warning;
- disk-space warning;
- transfer failure visibility;
- version/schema visibility;
- offline operation without false “system down” state.

## 15. Production readiness Central

Додатково перевірити:

- central health endpoints;
- DB monitoring;
- backup alerts;
- transfer receive/ACK errors;
- storage capacity;
- release identification.

## 16. Правило складності

Не додаємо monitoring component лише тому, що він типовий для великого SaaS.

Додаємо його, коли є конкретна operational проблема, яку він вирішує.
