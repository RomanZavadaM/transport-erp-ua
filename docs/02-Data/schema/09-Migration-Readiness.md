# PostgreSQL Physical Schema v1 — Migration Readiness Review

Статус: **M0 design review**

Мета: визначити, які рішення вже достатньо стабільні для майбутньої Alembic migration #1, а які потребують окремого підтвердження до написання DDL.

## 1. Готово до freeze

### Platform

- PostgreSQL 16+ baseline;
- extensions: `pgcrypto`, `citext`, `btree_gist`;
- UUID primary keys, recommended UUIDv7 application generation;
- `timestamptz` для instants;
- tenant `company_id`;
- RLS strategy;
- DB runtime/migration/reporting/backup roles;
- optimistic `row_version`;
- restrictive delete policy.

### Core domain boundaries

- Trip ≠ Duty;
- Duty contains 1..N Trips;
- planned assignments ≠ actual usage;
- Release belongs to Duty;
- plan ≠ fact;
- closed facts use immutable snapshots;
- Waybill uses immutable versions;
- corrections create new versions/snapshots;
- audit/events append-only.

### Concurrency

- `tstzrange [from,to)`;
- GiST exclusion for vehicle overlap;
- GiST exclusion for driver overlap;
- active Trip membership unique;
- atomic document numbering;
- row locks + canonical lock ordering;
- idempotency table.

### Versioning

- route versions with non-overlapping active periods;
- schedule versions with non-overlapping active periods;
- versioned check templates;
- versioned document templates + locale;
- historical Trip plan snapshot.

### History / evidence

- immutable trip snapshots;
- immutable waybill content versions;
- check invalidation instead of rewriting completed result;
- release evaluation batches;
- authorization history;
- correction cases;
- audit + partition sealing design.

## 2. Physical model coverage

Physical design currently covers **77 core tables**.

Every table belongs to one of:

- tenant/identity;
- fleet/drivers;
- routes/planning;
- trips;
- dispatch/duty;
- release/checks;
- documents/waybill;
- fuel;
- maintenance/repairs;
- corrections;
- audit/integration/operations.

Fields, key constraints, principal indexes and lifecycle policy are documented before DDL generation.

## 3. Items that MUST be resolved before migration #1

### MR-001 — Exact medical result code set

Current design allows conceptually:

- `FIT`;
- `UNFIT`;
- optionally `FIT_WITH_RESTRICTIONS`.

Before a rigid DB CHECK is created, legal/business review must decide the actual allowed set for Ukrainian deployment.

**Rule:** do not invent medical/legal semantics in migration.

### MR-002 — Waybill cardinality per Duty

Domain model supports Waybill → 1..N Trips.

Open question before partial UNIQUE:

- exactly one non-cancelled primary Waybill per Duty;
- or multiple document instances/types may legally/business-wise coexist.

Until confirmed, migration should not encode an irreversible overly restrictive constraint. If multiple types are required, introduce explicit `waybill_type/document_role` and constrain uniqueness by `(duty_id,type/role)`.

### MR-003 — Driver crew overlap inside one Duty

Global invariant is fixed: same driver cannot overlap across Duties.

Need confirm operational crew rules for:

- PRIMARY;
- SECOND_DRIVER;
- RELIEF;
- TRAINEE.

Only after this define any additional same-Duty exclusion beyond global driver conflict.

### MR-004 — Regulatory document type catalog

Tables are stable, but exact seeded types and `required_for_release / blocks_release_if_expired` values must come from verified regulatory/business catalog.

The schema does not block migration, but production seed data cannot be declared final before regulatory review.

### MR-005 — Operational day cutoff policy

`service_date` is explicit and stable.

Need decide whether automatic generation derives service date using configurable cutoff (e.g. 03:00) or schedule calendar only. This impacts application planning logic more than physical schema; no schema redesign expected.

### MR-006 — Waybill number format

Physical sequence supports series/year/prefix/suffix/next_value. Need approve actual numbering format and reset policy before production seeds/configuration, not before table creation.

### MR-007 — Object-storage retention / legal retention

`files` schema is stable. Exact retention/object-lock policy belongs to Issue #5 / regulatory review.

## 4. Items explicitly NOT blockers for migration #1

- GPS schema;
- ticketing;
- payroll;
- accounting;
- warehouse;
- external partner API;
- advanced analytics.

They are separate future bounded contexts and must not inflate core migration.

## 5. DDL generation rules

When migration #1 is written later:

1. create extensions;
2. create global/root reference tables;
3. create tenant/identity roots;
4. create fleet/drivers/routes/planning;
5. create trips/duties;
6. create release/checks;
7. create files/templates/waybills;
8. create fuel/maintenance/corrections;
9. create audit/outbox/system;
10. add cyclic/deferred FK such as effective/current version pointers;
11. add exclusion constraints and specialized indexes;
12. enable RLS/policies;
13. apply grants/immutable protections;
14. create partitions/default partition strategy;
15. seed only stable technical dictionaries/permissions;
16. run schema acceptance tests.

## 6. Migration acceptance tests

Migration #1 is acceptable only if automated PostgreSQL tests prove:

- clean database upgrades to head;
- expected extensions enabled;
- all PK/FK/UNIQUE/CHECK/EXCLUDE exist;
- cross-company composite FK rejected;
- vehicle overlap rejected;
- driver overlap rejected;
- duplicate generated Trip rejected;
- duplicate Waybill number rejected;
- runtime role cannot UPDATE/DELETE immutable tables;
- runtime role cannot bypass RLS;
- tenant A cannot read/write tenant B rows;
- closed historical evidence survives correction flow;
- migration can be recreated from an empty database reproducibly.

## 7. Architecture freeze decision

Issue #3 може бути закритий після review цього design, тому що structural physical schema визначена.

`MR-*` items переходять у regulatory/business configuration review і повинні бути вирішені **до написання відповідного rigid constraint/seed**, а не шляхом припущення.

Це дозволяє не змішувати два різні типи невизначеності:

- **архітектурна** — уже вирішена;
- **нормативна/операційна політика** — повинна бути підтверджена джерелом або власником процесу.