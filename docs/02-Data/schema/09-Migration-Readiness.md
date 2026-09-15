# Migration Readiness — Local SQLite + Central PostgreSQL

Статус: **architecture-v1.6 review before M1.5**

## 1. Що вже зроблено

Architecture-v1.5 і M1.3 довели PostgreSQL server schema/invariants та Alembic lifecycle на central/server profile.

Ця робота не втрачається.

Architecture-v1.6 додає другий physical profile — **Local SQLite** — і робить його першим practical target для подальших business modules.

## 2. Незмінне доменне ядро

Не переглядаються:

- UUID business identifiers;
- `Trip != Duty`;
- Duty 1..N Trips;
- planned assignments != actual usage;
- Release → Duty;
- Plan != Fact;
- immutable closed snapshots/versions;
- append-only audit;
- atomic business numbering;
- idempotency там, де команда реально може повторитися;
- route/schedule/check/document versioning;
- correction workflow.

## 3. Що більше не є universal physical requirement

Наступні PostgreSQL features залишаються Central defense-in-depth, але не є Local prerequisites:

- PostgreSQL 16+ як локальна БД;
- `pgcrypto` / `citext` / `btree_gist`;
- RLS;
- composite tenant-aware FK як обов’язковий local pattern;
- `tstzrange`;
- GiST exclusion constraints;
- DB runtime/reporting/backup roles;
- partitioning;
- `FOR UPDATE SKIP LOCKED`.

## 4. Local SQLite migration target

M1.5 повинна створити SQLite schema, яка підтримує той самий business contract.

Minimum:

- application-generated UUID;
- FK enabled;
- UNIQUE/CHECK;
- indexes;
- optimistic `row_version`;
- exact date/time serialization;
- exact numeric round-trip policy;
- audit;
- authority/transfer tables;
- backup/restore metadata;
- local immutability/read-only protections для critical records.

## 5. Transfer additions v1.6

Local schema потребує physical support для:

- node identity;
- authority state;
- transfer batches;
- transfer items;
- local approval metadata;
- delivery retry state;
- central ACK/receipt;
- central version/checksum metadata.

Central schema потребує:

- registered origin node/reference;
- idempotent receive key (`origin_node_id + transfer_batch_id` або equivalent);
- receipt/ACK;
- origin/version provenance для прийнятих даних.

## 6. Regulatory/business review

Регуляторні рішення MR-001..MR-007 з architecture-v1.5 залишаються чинними. Зміна physical DB profile не змінює їх зміст.

Зокрема:

- medical result `FIT|UNFIT`;
- multiple drivers/crew support;
- context-aware document requirements;
- explicit `service_date`;
- generic configurable Waybill numbering;
- correction workflow;
- retention policy як enterprise/legal configuration.

Повний реєстр: `docs/10-Legal/MR-Decision-Register.md`.

## 7. Local numbering

Оскільки local node має працювати offline, numbering strategy не може вимагати online central sequence для кожного документа.

До M6 треба затвердити practical series/prefix/range policy для кількох автономних local nodes.

Для одного local node звичайна local atomic sequence достатня.

## 8. Local migration acceptance tests M1.5

Обов’язково довести:

1. clean SQLite DB створюється автоматично при first run;
2. FK реально enabled;
3. schema upgrade виконується на копії/fixture;
4. failed migration має recovery path;
5. UUID/date/time/decimal values round-trip без зміни semantics;
6. audit записується атомарно з critical mutation;
7. `CENTRAL` record не можна змінити local business command;
8. transfer не стартує без local approval;
9. interrupted delivery не переводить authority у `CENTRAL`;
10. duplicate delivery не дублюється central;
11. valid ACK переводить records у local read-only;
12. SQLite backup → restore відтворює DB + transfer state;
13. documents manifest/checksum переживає restore.

## 9. Central PostgreSQL acceptance tests

Зберігаємо existing server tests та додаємо:

- idempotent transfer receive;
- unique transfer receipt;
- origin/checksum validation;
- central update versioning;
- PostgreSQL resource-conflict constraints;
- RLS тільки там, де central deployment його реально використовує.

## 10. DDL / migration strategy

Не намагаємося мати один буквальний SQL-файл для SQLite і PostgreSQL.

Маємо один domain/application contract і дві перевірені physical migration paths.

Де можливо — shared SQLAlchemy metadata/migration helpers. Де physical feature відрізняється — явний dialect-specific migration code з окремими tests.

## 11. Existing detailed schema files

`01-Organization-Identity.md` .. `05-Waybills-Fuel-Maintenance.md` походять з PostgreSQL-oriented v1.5 design.

До реалізації відповідного M2–M6 модуля кожна таблиця проходить practical SQLite adaptation review.

Не потрібно переписувати всі 77 таблиць наперед до M1.5, якщо модуль ще не реалізується. Потрібно зараз створити правильні shared conventions та foundation tables, а domain tables переносити по milestone.

## 12. Що є blocker до M2

Blocker:

- SQLite local application starts cleanly;
- migration lifecycle працює;
- authority/transfer foundation працює;
- backup/restore працює;
- desktop packaging spike доводить реальний single-PC сценарій.

Не blocker:

- GPS;
- ticketing;
- payroll;
- parts warehouse;
- S3;
- Redis;
- Kubernetes;
- advanced central analytics;
- full rewrite усіх майбутніх domain DDL до SQLite до того, як ці модулі почнуть реалізовуватися.

## 13. Практичне правило

Перед реалізацією кожного наступного domain module:

1. взяти v1.5 logical/physical design як вихідну специфікацію;
2. визначити мінімальну SQLite local schema;
3. додати portable business constraints/tests;
4. залишити PostgreSQL-specific constraints як central enhancement;
5. не будувати infrastructure “на виріст”, якщо немає конкретного use case.
