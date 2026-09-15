# PostgreSQL Schema — Organization & Identity

## companies

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| legal_name | text | NOT NULL |
| edrpou | varchar(10) | NOT NULL, UNIQUE |
| timezone | varchar(64) | NOT NULL, default policy `Europe/Kyiv` |
| default_locale | varchar(5) | NOT NULL DEFAULT `uk` |
| status | varchar(20) | NOT NULL |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

CHECK:

- `status IN ('ACTIVE','SUSPENDED')`;
- `default_locale IN ('uk','en','es','fr','de')`;
- `char_length(edrpou) BETWEEN 8 AND 10`.

Indexes:

- UNIQUE `edrpou`;
- `ix_companies_status(status)`.

## company_settings

| Поле | Тип | Правила |
|---|---|---|
| company_id | uuid | PK/FK companies |
| settings | jsonb | NOT NULL DEFAULT `{}` |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | FK users nullable |
| row_version | bigint | NOT NULL DEFAULT 1 |

Використовується лише для configuration values, що не заслуговують окремої relational table. Critical business policy з окремими query/constraints не слід ховати в цей JSON.

## depots

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL FK companies |
| code | varchar(30) | NOT NULL |
| name | text | NOT NULL |
| address | text | NULL |
| timezone | varchar(64) | NULL; fallback company timezone |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id, code)`;
- UNIQUE `(company_id, id)` для tenant-aware child FK.

Indexes:

- `(company_id, active)`.

## users

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL FK companies |
| username | citext | NOT NULL |
| email | citext | NULL |
| password_hash | text | NOT NULL |
| status | varchar(20) | NOT NULL |
| preferred_locale | varchar(5) | NULL |
| driver_id | uuid | NULL; optional link to driver identity |
| last_login_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL FK users |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL FK users |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id, username)`;
- UNIQUE `(company_id, email)` WHERE email IS NOT NULL;
- UNIQUE `(company_id, id)`;
- CHECK `status IN ('ACTIVE','SUSPENDED','DISABLED')`;
- CHECK preferred_locale IS NULL OR preferred_locale IN supported locales.

`driver_id` tenant consistency забезпечується composite FK після створення `drivers`.

Фізичне видалення користувача, який є actor в історії, не підтримується; використовується `DISABLED`.

## user_sessions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| user_id | uuid | NOT NULL |
| token_hash | char(64) | NOT NULL UNIQUE |
| created_at | timestamptz | NOT NULL |
| expires_at | timestamptz | NOT NULL |
| revoked_at | timestamptz | NULL |
| rotated_from_id | uuid | NULL self-FK |
| ip_address | inet | NULL |
| user_agent | text | NULL |

FK `(company_id,user_id)` → users `(company_id,id)`.

CHECK `expires_at > created_at`.

Indexes:

- `(user_id, expires_at)`;
- partial `(expires_at)` WHERE revoked_at IS NULL.

Retention short-lived; expired sessions may be safely purged by maintenance policy.

## roles

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL for system template, otherwise tenant |
| code | varchar(80) | NOT NULL |
| name | text | NOT NULL |
| system_role | boolean | NOT NULL DEFAULT false |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |

Constraints:

- UNIQUE `(company_id, code)`; null/system role uniqueness handled by appropriate partial unique index;
- role code is technical stable identifier.

## permissions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| code | varchar(120) | NOT NULL UNIQUE |
| description | text | NOT NULL |
| domain | varchar(50) | NOT NULL |

Permission codes відповідають `docs/03-API/Permissions-Catalog.md`.

## user_roles

| Поле | Тип | Правила |
|---|---|---|
| company_id | uuid | NOT NULL |
| user_id | uuid | NOT NULL |
| role_id | uuid | NOT NULL |
| assigned_at | timestamptz | NOT NULL |
| assigned_by | uuid | NULL |

PK `(user_id, role_id)`.

FK user → users RESTRICT/CASCADE association policy; FK role → roles. Видалення association допустиме, але зміна обов’язково audit-иться.

## role_permissions

| Поле | Тип | Правила |
|---|---|---|
| role_id | uuid | NOT NULL |
| permission_id | uuid | NOT NULL |

PK `(role_id, permission_id)`.

`ON DELETE CASCADE` допустимий як association-only row.

## api_idempotency_keys

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| actor_user_id | uuid | NOT NULL |
| command_scope | varchar(180) | NOT NULL |
| idempotency_key | varchar(200) | NOT NULL |
| request_hash | char(64) | NOT NULL |
| response_status | integer | NULL |
| response_body | jsonb | NULL |
| result_entity_type | varchar(80) | NULL |
| result_entity_id | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| expires_at | timestamptz | NOT NULL |

Constraint:

UNIQUE `(company_id, actor_user_id, command_scope, idempotency_key)`.

Index partial `(expires_at)` for cleanup.

## security/login audit

Окрему mutable `login_history` таблицю не вводимо як source of truth. Security-sensitive auth events пишуться до append-only audit/security logging stream із retention policy. Якщо обсяг потребуватиме окремої таблиці — це буде спеціалізована append-only partitioned table, а не частина user row.

## Tenant/RLS

RLS policy застосовується до tenant tables через `company_id`.

`permissions` може бути global reference table без RLS. System role templates із `company_id NULL` читаються через окрему policy/view; tenant-created roles із company_id ізольовані.
