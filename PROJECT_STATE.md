# PROJECT_STATE

## Поточний baseline

Стабільний main baseline: **architecture-v1.5**.  
Робочий архітектурний перегляд: **architecture-v1.6-local-first**.  
Канонічна мова: **українська (`uk`)**; переклади: `en`, `es`, `fr`, `de`.

**M1.5 implementation paused until architecture-v1.6 local-first review is merged.**

## Product scope

TransportERP-UA — ERP насамперед **одного автотранспортного підприємства**, яке може бути дуже малим або великим.

Система повинна бути практично придатною для:

- малого АТП приблизно на 5–10 машин, де все працює на одному звичайному комп’ютері;
- середнього підприємства;
- великого підприємства з кількома локальними вузлами та центральним рівнем.

Не створюємо окрему `Lite` edition.

## Local-first рішення architecture-v1.6

### Локальний рівень

Базовий production deployment — **встановлюваний desktop-застосунок TransportERP-UA**.

Користувач запускає програму з ярлика. Робота через вкладку браузера/`localhost` не є базовою користувацькою моделлю.

Локальний вузол містить:

- desktop application shell;
- локальний backend;
- SQLite;
- локальний каталог документів;
- backup/restore;
- transfer client.

Локальний користувач не повинен встановлювати або адмініструвати PostgreSQL, Docker, Redis чи S3.

### Джерело істини та передача на вищий рівень

Business authority має лише два стани:

- `LOCAL` — локальна SQLite є джерелом істини, local edit дозволений;
- `CENTRAL` — central ACK отримано, local copy read-only, редагування виконується на central.

**До valid central ACK authority завжди залишається `LOCAL`.**

Transfer workflow має окремі статуси, наприклад `PENDING_APPROVAL`, `TRANSFERRING`, `FAILED`, `ACKNOWLEDGED`, `CANCELLED`. Вони не означають зміну джерела істини.

Передача може бути підготовлена:

- добровільно локальним оператором;
- запитом зверху;
- правилом/розкладом.

Але фактична передача **завжди підтверджується оператором на локальному вузлі**.

Після local approval payload/versions фіксуються. На час активної передачі records можуть мати тимчасовий transfer lock, щоб approved data не змінилися в дорозі. Це не зміна authority.

Після успішної передачі та valid central ACK:

- authority переходить `LOCAL → CENTRAL`;
- передані дані локально стають read-only;
- local backend забороняє їх зміну;
- central може повернути новішу read-only версію на local.

Невдала/перервана передача не переводить authority у `CENTRAL`.

Канонічний ADR: `docs/01-Architecture/ADR/ADR-0007-Local-SQLite-and-Central-Transfer.md`.

## Центральний рівень

Central є опційним вищим рівнем і може використовувати PostgreSQL.

Його практичні задачі:

- приймання схвалених локальних transfer batches;
- редагування вже переданих даних;
- консолідована звітність;
- централізоване управління там, де воно потрібне.

Central outage не повинен зупиняти локальну роботу з даними authority=`LOCAL`.

## Frozen domain decisions, які залишаються

- Modular Monolith.
- `Trip != Duty`; Duty містить 1..N Trips.
- `Release` належить Duty.
- Waybill — versioned enterprise document, пов'язаний з Duty і 1..N Trips.
- Plan і Fact розділені.
- CLOSED history immutable; correction створює новий snapshot/version.
- Audit append-only.
- Critical commands transactional та idempotent там, де повтор реально можливий.
- Optimistic locking захищає від lost update.
- Frontend/desktop shell не є джерелом бізнес-рішень.

## Переглянуті infrastructure decisions

Architecture-v1.5 рішення `PostgreSQL everywhere` більше не є цільовим.

- SQLite — operational DB local node.
- PostgreSQL — central/server DB.
- S3 не обов'язковий; local використовує filesystem.
- Redis не обов'язковий.
- Docker не обов'язковий для local desktop.
- single-PC є повноцінним production deployment, не pilot/fallback.
- outbox — технічна надійна доставка, а не складна integration platform.
- observability local має бути практичною і легкою; server-grade monitoring належить central profile.

## M0 / M1 historical implementation state

### M1.1 Application skeleton + CI — DONE
Merged to `main` as `f85c6b9…`.

### M1.2 Consolidated OpenAPI — DONE
Merged to `main` as `27ac384…`.

### M1.3 Alembic migration #1 + PostgreSQL invariants — DONE
Merged to `main` as `d64c765b9ed6ee7acdf1add12fbf4ae26edeeba8`.

Це залишається корисною server/central implementation базою, але physical schema має отримати SQLite-compatible local profile.

### M1.4 Identity and access foundation — DONE
Merged to `main` as `7d17edf737cc344037bed3ee4ade6ecbb689b2cc`.

Залишаються корисними password/session security, RBAC/permissions, stable error envelope/request ID та identity application/domain separation.

PostgreSQL-specific RLS, `SET LOCAL app.company_id`, DB roles та `SECURITY DEFINER` розглядаються як central/server implementation, а не обов'язкова local SQLite dependency.

## M1.5 — REDEFINED / NEXT

Issue #20 переглянуто під architecture-v1.6.

Практичний порядок M1.5:

1. local SQLite database profile + migrations;
2. application data directories та filesystem storage abstraction;
3. append-only local audit;
4. authority=`LOCAL|CENTRAL` + transfer lock;
5. transfer batch status/approval flow;
6. local approval у UI/API;
7. reliable delivery/outbox;
8. central receipt/ACK contract та idempotent receive;
9. `LOCAL → CENTRAL` тільки після valid ACK;
10. local read-only enforcement після ACK;
11. backup/restore local SQLite + files;
12. lightweight local health/integrity checks;
13. desktop packaging spike та production launcher behavior;
14. acceptance tests: offline work, interrupted transfer, ACK lock, backup/restore;
15. CI green before merge.

Не є M1.5 prerequisites:

- Redis;
- Kafka/RabbitMQ;
- Kubernetes;
- S3;
- multi-worker queue;
- Prometheus/Grafana stack;
- audit partitioning;
- multi-master conflict resolution.

Після M1.5 проект переходить до **M2 Fleet & Drivers** вже на local-first foundation.

## Regulatory baseline

State verified on 15.09.2026. Canonical documents are under `docs/10-Legal/`.
Traceability: `source → MR decision → BR-* → API/DB/policy → AT-*`.

## Deferred

GPS/live monitoring, passenger accounting/e-ticketing, mobile driver app, payroll/accounting, fuel-card integration, parts warehouse, external route-passport integration, advanced analytics, server-scale optimization.

## Repository governance

- `docs/` — canonical Obsidian Vault;
- significant changes — branch + Pull Request;
- accepted ADR are not silently rewritten: superseded ADR зберігаються з відповідним статусом;
- Business Rule IDs: `BR-*`;
- Acceptance Test IDs: `AT-*`;
- secrets and production data are never stored in Git.
