# PostgreSQL Physical Schema v1 — Конвенції

Статус: **M0 physical design draft**  
Пов’язаний issue: **#3**

## 1. PostgreSQL

Ціль: PostgreSQL 16+ для production baseline.

Required extensions:

- `pgcrypto` — UUID/crypto utilities за потреби;
- `citext` — case-insensitive email/login fields;
- `btree_gist` — exclusion constraints із UUID/company keys.

## 2. Primary keys

Основні бізнес-таблиці:

`id uuid PRIMARY KEY`

Рекомендація для application-generated ID: UUIDv7.

DB не покладається на послідовний integer ID як зовнішній API identifier.

## 3. Tenant key

Основні company-scoped таблиці мають:

`company_id uuid NOT NULL`

Для критичних cross-tenant relations parent таблиця додатково має:

`UNIQUE (company_id, id)`

а child використовує composite FK:

`FOREIGN KEY (company_id, parent_id) REFERENCES parent(company_id,id)`.

Це фізично забороняє зв’язок сутностей різних підприємств.

## 4. Timestamps

Моменти часу:

`timestamptz`

Business date:

`date`

Час у розкладі без конкретної дати:

`time without time zone`

Company timezone зберігається як IANA name, наприклад `Europe/Kyiv`.

## 5. Common mutable aggregate columns

Для mutable aggregate root:

- `created_at timestamptz NOT NULL DEFAULT now()`;
- `created_by uuid NULL/NOT NULL according to context`;
- `updated_at timestamptz NOT NULL DEFAULT now()`;
- `updated_by uuid NULL`;
- `row_version bigint NOT NULL DEFAULT 1`.

`row_version` змінюється при meaningful update і є основою ETag/If-Match.

## 6. Delete policy

Operational/history tables:

`ON DELETE RESTRICT` / `NO ACTION`.

`ON DELETE CASCADE` дозволено лише для технічних association rows, наприклад:

- `user_roles`;
- `role_permissions`;
- draft-only child configuration, якщо parent ще не використано історично.

Closed business history не видаляється.

## 7. Status fields

State-machine values зберігаються як `varchar(32)` / `text` + CHECK, а не PostgreSQL ENUM.

Причина: контрольовані migrations простіші, а технічні codes залишаються стабільними.

## 8. Time ranges

Assignment/usage periods:

`tstzrange`

Canonical bounds:

`[from,to)`.

CHECK:

- range not empty;
- lower bound not null;
- upper bound not null.

Adjacent periods `08:00–10:00` і `10:00–12:00` не конфліктують.

## 9. Numeric policy

- odometer: `bigint` kilometers для MVP;
- distance: `numeric(12,3)`;
- fuel: `numeric(12,3)`;
- money: `numeric(14,2)`;
- unit price: `numeric(14,4)`;
- coordinates: `numeric(9,6)`.

## 10. JSONB

`jsonb` використовується лише там, де структура справді versioned/extensible:

- immutable snapshots;
- rule details/configuration;
- audit before/after;
- integration payload;
- template schema.

Core relational fields не ховаються в JSONB.

## 11. Immutability

Append-only / immutable після insert:

- `audit_log`;
- `trip_events`;
- `duty_events`;
- `waybill_versions`;
- `trip_actual_snapshots`;
- `release_rule_evaluations`;
- completed check data після completion;
- historical correction evidence.

Protection: DB grants + triggers where required.

## 12. Soft delete vs business state

Не використовувати generic `deleted_at` для operational history.

Замість цього business states:

- `CANCELLED`;
- `REVOKED`;
- `SUPERSEDED`;
- `DECOMMISSIONED`;
- `TERMINATED`.

Master/reference data може мати `active boolean` або archive state.

## 13. Index naming

Convention:

- PK: automatic / `pk_<table>`;
- unique: `uq_<table>_<fields>`;
- index: `ix_<table>_<fields>`;
- check: `ck_<table>_<meaning>`;
- FK: `fk_<table>_<field>_<parent>`;
- exclusion: `ex_<table>_<meaning>`.

## 14. RLS context

Runtime transaction встановлює company context через `SET LOCAL`/equivalent transaction-local setting.

Runtime DB role:

- не superuser;
- не `BYPASSRLS`;
- не owner критичних tables.

## 15. DB roles

Передбачити:

- `migration_role` — DDL;
- `app_runtime_role` — business DML за grants/RLS;
- `reporting_role` — read-only views/read models;
- `backup_role` — backup-specific minimum privileges.

## 16. Migration principle

Physical design є основою Alembic migration #1, але schema повинна створюватися migrations, а не ручним production SQL.

Зміни production schema: expand → migrate/backfill → contract, коли потрібна backward compatibility.