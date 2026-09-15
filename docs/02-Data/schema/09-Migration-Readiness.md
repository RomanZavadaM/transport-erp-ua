# PostgreSQL Physical Schema v1 — Migration Readiness Review

Статус: **M0 regulatory review completed 15.09.2026**

Мета: визначити, які рішення достатньо стабільні для майбутньої Alembic migration #1 та які deployment policy залишаються конфігураційними.

## 1. Structural architecture — READY

Готово до freeze:

- PostgreSQL 16+ baseline;
- `pgcrypto`, `citext`, `btree_gist`;
- UUID PK;
- `timestamptz` для instants;
- tenant `company_id` + tenant-aware FK/RLS;
- restrictive delete policy;
- optimistic `row_version`;
- `Trip != Duty`;
- Duty 1..N Trips;
- planned assignments != actual usage;
- Release → Duty;
- plan != fact;
- immutable closed snapshots/versions;
- append-only audit/events;
- `tstzrange [from,to)`;
- GiST exclusion resource conflicts;
- atomic document numbering;
- idempotency;
- route/schedule/check/document versioning;
- correction workflow;
- outbox/integrity architecture.

Physical design covers **77 core tables**.

## 2. Regulatory/business review results

Повний decision register: [`../../10-Legal/MR-Decision-Register.md`](../../10-Legal/MR-Decision-Register.md).

### MR-001 — Medical result

**RESOLVED / CONFIRMED**

Для щозмінного передрейсового workflow normalized result:

```text
FIT
UNFIT
```

`FIT_WITH_RESTRICTIONS` не включається у rigid result set цього check.

DB/API consequence:

- `fitness_result` CHECK → `FIT|UNFIT`;
- `UNFIT` blocks Release;
- completed check immutable; invalidation + replacement check.

### MR-002 — Waybill cardinality

**RESOLVED AS INTERNAL POLICY**

Закон №2344-III не дає підстав hardcode historical «дорожній лист» як універсально обов'язковий документ для регулярного passenger workflow.

Architecture decision:

- Waybill залишається enterprise operational/accounting document;
- рекомендований deployment policy — один `PRIMARY` Waybill на Duty;
- schema повинна дозволяти explicit document role/type, щоб майбутні додаткові document instances не ламали модель;
- не використовувати безумовне `UNIQUE(duty_id)` для всіх можливих document roles.

Перед migration implementation треба відобразити `document_role`/equivalent у waybill uniqueness design.

### MR-003 — Driver crew

**RESOLVED STRUCTURALLY**

Чинне Положення №340 передбачає crew driving щонайменше двома водіями.

Architecture consequence:

- multiple driver assignments/usage у Duty обов'язкові;
- global same-driver overlap між Duty заборонений;
- нормативний `crew_mode` відокремлюється від enterprise labels `PRIMARY/SECOND_DRIVER/RELIEF/TRAINEE`;
- не створювати regulatory DB invariant «рівно один PRIMARY на весь Duty».

### MR-004 — Regulatory document catalog

**RESOLVED AS CONTEXT RULE**

Стаття 39 Закону №2344-III має різні document requirements за видом перевезення.

Architecture consequence:

- document types залишаються довідниками;
- `required/blocking` визначається compliance rule version + transport/service context;
- не seed-ити один глобальний набір `required_for_release=true` для всіх Duty;
- carrier-level license/contract/route-passport evidence не змішується з `driver_documents`/`vehicle_documents`.

Це потребує rule seed data, але не зміни fundamental schema.

### MR-005 — Operational day cutoff

**RESOLVED AS INTERNAL POLICY**

- `service_date` explicit і immutable;
- cutoff optional company setting;
- зміна cutoff не перераховує history;
- M0 default: календарний operational date у company timezone без штучного cutoff, доки підприємство не затвердить інше.

### MR-006 — Waybill numbering

**RESOLVED AS INTERNAL POLICY**

- `number_sequences` залишається generic;
- series/year/prefix/suffix/next_value;
- issued number never reused;
- reset/format configurable, не DB law;
- рекомендований default — series by document type/year, якщо enterprise policy не визначає інакше.

### MR-007 — Retention/object lock

**RESOLVED ARCHITECTURALLY / LEGAL POLICY BEFORE PRODUCTION**

- retention by data/document class;
- no automatic purge of CLOSED history;
- legal hold/extended retention supported;
- primary accounting documents юридичної особи повинні враховувати applicable tax minimum (для відповідної категорії 1825 днів) та довші строки, якщо вони застосовуються;
- object-lock duration задається затвердженою enterprise retention matrix.

Retention matrix є production configuration/legal deliverable, але не blocker для створення core tables.

## 3. Додаткові regulatory corrections до design

### Technical checker

Наказ №974 не обмежує виконавця єдиною нормативною роллю «механік».

Implementation rule:

- domain concept: authorized/qualified `technical_checker`;
- UI role `MECHANIC` може надавати permission `technical_check.perform`;
- driver pre-departure technical check/evidence моделюється окремо від іншої technical inspection;
- failed/blocking technical result blocks Release.

### Route passport external identity

Новий Порядок, чинний з 13.07.2026, переводить route passports до державного Єдиного комплексу.

Core migration не повинна дублювати зовнішній registry, але future integration має мати external identifier/reference/sync metadata.

Це post-MVP integration і не блокує migration #1.

## 4. Що залишається до migration #1

Не normative unknowns, а implementation preparation:

1. відобразити `waybill document_role/type` у detailed DDL design;
2. уточнити technical driver-predeparture evidence table/field mapping;
3. сформувати context-aware compliance seed structure;
4. затвердити stable technical permission/status seed list;
5. створити migration acceptance tests;
6. написати Alembic migration тільки **після фінального M0 Architecture Freeze**.

## 5. Не blockers для migration #1

- GPS;
- ticketing;
- payroll;
- accounting integration;
- parts warehouse;
- external route-passport API integration;
- advanced analytics;
- final legal retention matrix values.

## 6. DDL generation order

1. extensions;
2. root/reference tables;
3. tenant/identity;
4. fleet/drivers/routes/planning;
5. trips/duties;
6. release/checks;
7. files/templates/waybills;
8. fuel/maintenance/corrections;
9. audit/outbox/system;
10. cyclic/deferred current-version FK;
11. exclusions/specialized indexes;
12. RLS;
13. grants/immutable protections;
14. partitions;
15. stable technical seeds;
16. schema acceptance tests.

## 7. Migration acceptance tests

Migration #1 повинна довести:

- clean DB upgrades to head;
- expected extensions;
- PK/FK/UNIQUE/CHECK/EXCLUDE;
- cross-company FK rejected;
- resource overlap rejected;
- duplicate generated Trip rejected;
- duplicate Waybill number rejected;
- invalid medical result rejected;
- runtime role cannot mutate immutable history;
- RLS tenant isolation;
- context-rule seed structure is reproducible;
- migration recreates schema from empty DB reproducibly.

## 8. Freeze decision

Після regulatory review **немає невирішеної нормативної невизначеності, яка вимагала б перепроєктування core aggregates**.

Залишаються enterprise configuration/policy values, які повинні бути versioned/configurable і затверджуватися без зміни фундаментальної архітектури.
