# Definition of Done — Production MVP

Статус: **M0 draft**

MVP вважається готовим не тоді, коли “екрани відкриваються”, а коли повний operational workflow працює без логічних суперечностей, захищений тестами та може бути безпечно відновлений після збою.

## 1. Архітектура

- M0 Architecture Freeze завершено;
- усі accepted ADR актуальні;
- українська документація є канонічною;
- `Trip != Duty` реалізовано без shortcut-зв’язків;
- plan і fact зберігаються окремо;
- closed history використовує immutable snapshots/versions;
- corrections не reopen-ять закриту історію;
- domain modules не обходять application services довільним cross-table CRUD.

## 2. База даних

- усі migrations versioned в Git;
- schema відтворюється з нуля автоматично;
- PK/FK/UNIQUE/CHECK/EXCLUDE constraints відповідають design;
- overlapping active vehicle assignment неможливий на DB level;
- overlapping active driver assignment неможливий на DB level;
- один Trip не може бути у двох active Duty;
- document/waybill numbering concurrency-safe;
- tenant isolation перевірена;
- closed/append-only data захищені від несанкціонованого UPDATE/DELETE;
- indexes перевірені для основних operational queries;
- production DB user не має зайвих DDL/admin прав.

## 3. Backend / API

- OpenAPI v1 відповідає затвердженому contract;
- critical transitions мають explicit command endpoints;
- generic status mutation відсутня;
- permission checks виконуються на backend;
- optimistic locking працює для mutable aggregates;
- critical repeatable POST підтримують Idempotency-Key;
- business conflicts повертають стабільні machine-readable error codes;
- `409 Conflict` використовується для concurrency/resource conflicts;
- critical commands атомарно створюють audit/outbox/event data;
- fresh compliance evaluation виконується при release authorization;
- API не довіряє frontend-calculated critical result.

## 4. Frontend

- реалізовані всі MVP screens із `Screen-Catalog.md`;
- UI локалізований `uk/en/es/fr/de` на рівні закладеної M0 i18n architecture;
- `uk` — default locale;
- критичні status transitions виконуються action buttons;
- причини блокування видимі текстом;
- stale update не перетирає нові дані;
- dispatcher board показує актуальний operational state;
- Release Workspace дає повний decision context;
- closed entities відображаються read-only;
- responsive behavior прийнятний для підтримуваних desktop/tablet viewport;
- keyboard/focus/basic accessibility перевірені для основних форм.

## 5. Наскрізний бізнес-процес

На production-like environment автоматично та вручну пройдено сценарій:

1. створені vehicle/driver/documents;
2. створені stops/route/version;
3. створений schedule/version;
4. згенеровано Trip;
5. створено Duty;
6. призначено vehicle і driver;
7. пройдено medical check;
8. пройдено technical check;
9. compliance PASS;
10. dispatcher authorization;
11. Waybill number + PDF;
12. actual departure;
13. Trip execution/completion;
14. Duty return;
15. Trip close;
16. Duty close;
17. Waybill close;
18. дані з’явилися у reports/audit.

Сценарій повторюється для failure path: blocking document/check/defect повинен зупинити release.

## 6. Конкурентність

Автоматичні тести доводять:

- 20 concurrent conflicting vehicle assignments → максимум один success;
- 20 concurrent conflicting driver assignments → максимум один success;
- duplicate authorize request не створює два authorizations;
- duplicate Waybill request не видає два номери;
- stale ETag/row_version → conflict, не overwrite;
- deadlock/serialization retry policy не створює duplicate side effects.

## 7. Audit / history

- усі critical business commands мають audit entry;
- audit містить actor, time, entity, action, request/correlation id;
- sensitive fields не потрапляють у логи без потреби;
- Waybill versions immutable;
- Trip close створює immutable actual snapshot;
- correction створює new version/snapshot із reason і link до previous;
- physical delete closed Trip/Waybill неможливий через application workflow;
- audit UI дозволяє відтворити ключову послідовність подій.

## 8. PDF / Waybill

- numbering atomic і unique;
- template version збережена;
- snapshot schema version збережена;
- original PDF збережений в object storage;
- SHA-256 snapshot/PDF збережений;
- повторне відкриття/друк повертає historical document;
- зміна master data не змінює старий PDF;
- correction не перезаписує попередню version.

## 9. Reports

Усі обов’язкові MVP reports:

- мають correct filters;
- перевірені на reference dataset;
- поважають company/permission scope;
- не читають дані іншого tenant;
- не блокують operational API неприйнятно довго;
- важкі exports, якщо є, виконуються worker-ом.

## 10. Security

- HTTPS enforced у production;
- password hashing — modern approved algorithm;
- session/token storage відповідає security design;
- browser auth не залежить від long-lived token у localStorage;
- CSRF strategy перевірена;
- XSS protections/CSP визначені;
- SQL injection покривається parameterized data access + tests;
- rate limiting для auth/critical public endpoints;
- object access перевіряє permissions/company scope;
- IDOR tests пройдені;
- secrets відсутні у Git history;
- dependency/security scanning підключено або задокументовано як production gate.

## 11. Backup / Disaster Recovery

- PostgreSQL backup працює автоматично;
- WAL/PITR policy налаштована відповідно до затвердженого RPO/RTO;
- object storage входить у backup strategy;
- documented restore runbook існує;
- виконано реальний restore у temporary environment;
- restored system проходить integrity checks;
- backup failure формує alert;
- остання успішна restore test має зафіксовану дату.

## 12. Observability

- structured logs;
- request_id/correlation_id;
- `/health/live`;
- `/health/ready`;
- DB connection/latency monitoring;
- worker/outbox monitoring;
- failed jobs visible;
- integrity alerts visible;
- критичні production errors не губляться лише в stdout.

## 13. Performance baseline

До запуску мають бути зафіксовані реальні очікувані обсяги підприємства.

Мінімально перевіряємо:

- dispatcher board за робочий день;
- списки Trips/Duties;
- release authorization;
- document expiry dashboard;
- Waybill generation;
- reports за типовий місяць;
- concurrency assignment tests.

Немає вимоги оптимізувати під мільйони GPS points у MVP — GPS є post-MVP domain.

## 14. Testing gate

CI не дозволяє merge при failure обов’язкових suites:

- unit;
- domain;
- PostgreSQL integration;
- API;
- permissions;
- concurrency;
- state-machine transition matrix;
- critical end-to-end;
- migration tests.

PDF visual regression та security tests входять у release gate згідно з test strategy.

## 15. Документація

Перед production launch актуальні:

- README;
- PROJECT_STATE;
- architecture version;
- ADR;
- ERD/data model;
- OpenAPI;
- business rules;
- permission matrix;
- operational runbook;
- backup/restore runbook;
- deployment instructions;
- support/troubleshooting notes;
- release notes.

Українська версія є source of truth. Translation status для EN/ES/FR/DE не повинен блокувати emergency technical fix, але користувацькі тексти нової функції мають мати locale resources до production release.

## 16. Release gate

Production MVP дозволено випустити лише якщо:

- немає open blocker/critical defect;
- всі acceptance tests `AT-*` для MVP PASS;
- DB migrations перевірені на clean install та upgrade path;
- backup/restore test PASS;
- security review PASS;
- operational owner підтвердив наскрізний workflow;
- release tag і changelog підготовлені.

## 17. Що не є причиною затримати MVP

Не є дефектом MVP відсутність функцій, які явно віднесені до post-MVP:

GPS, ticketing, payroll, accounting, native mobile app, full warehouse, external partner API, advanced BI.

Їх не можна непомітно додавати в scope під час фінального acceptance.