# Physical Schema Conventions — Local SQLite + Central PostgreSQL

Статус: **architecture-v1.6 baseline**

## 1. Один логічний model, два physical profiles

### Local
SQLite — базова operational БД desktop-застосунку.

### Central
PostgreSQL 16+ — рекомендована серверна БД центрального рівня.

Application/domain code не повинен вимагати PostgreSQL-specific типів для звичайної локальної роботи.

## 2. Primary keys

Business identifiers генеруються application-side як UUID.

Логічний тип: `UUID`.

- Local SQLite: стабільне textual UUID representation;
- Central PostgreSQL: native `uuid`.

Зовнішній API не використовує auto-increment integer як business identifier.

## 3. Company context

`company_id` лишається у model для enterprise identity та central consolidation.

Local node зазвичай має один активний enterprise context, тому RLS усередині SQLite не емулюється.

Central PostgreSQL може використовувати composite FK/RLS там, де це виправдано.

## 4. Час і дати

Логічні типи:

- moment — timezone-aware datetime;
- business/service date — date;
- schedule local time — time.

Правило:

- moments canonical зберігаються/передаються в UTC;
- company/display timezone зберігається як IANA name, наприклад `Europe/Kyiv`;
- Local SQLite використовує однозначне ISO-8601 representation через persistence adapter;
- Central PostgreSQL використовує `timestamptz`/`date`/`time`.

Не покладатися на SQLite server timezone.

## 5. Common mutable aggregate columns

Логічно:

- `created_at`;
- `created_by`;
- `updated_at`;
- `updated_by`;
- `row_version bigint/int64 DEFAULT 1`.

`row_version` збільшується при meaningful update і використовується для optimistic locking.

## 6. Delete policy

Operational/history data не видаляється фізично звичайним користувацьким flow.

FK default: RESTRICT/NO ACTION semantics.

CASCADE допускається для технічних association rows, які не мають окремої історичної цінності.

Business lifecycle використовує `CANCELLED`, `REVOKED`, `SUPERSEDED`, `DECOMMISSIONED`, `TERMINATED` тощо замість generic `deleted_at`.

## 7. Status fields

Стабільні text codes + CHECK/application validation.

Не використовуємо PostgreSQL ENUM як доменну необхідність.

SQLite і PostgreSQL повинні приймати однаковий набір codes.

## 8. Assignment/usage periods

Логічно period має `from` і `to` з семантикою `[from,to)`.

### Local SQLite
Зберігаються окремі `*_from` / `*_to` timestamps. Overlap перевіряє backend усередині controlled write transaction; потрібні indexes по resource + from/to.

### Central PostgreSQL
Можна додатково використовувати `tstzrange`/GiST exclusion як defense-in-depth.

Core domain не залежить від range type.

## 9. Exact numeric values

API/domain використовує exact decimal semantics для:

- distance;
- fuel;
- money;
- unit price.

Local SQLite implementation **не повинна тихо переводити exact business values у binary float**.

До M2 physical implementation має обрати та протестувати один portable mapping:

- scaled integer storage для полів із фіксованою точністю; або
- інший exact serialization adapter з guaranteed round-trip.

Central PostgreSQL використовує `numeric(p,s)`.

Acceptance tests повинні доводити однаковий round-trip Local ↔ Central для граничних значень.

## 10. JSON / extensible payloads

Логічний JSON використовується лише для справді extensible/versioned data:

- immutable snapshot details;
- audit before/after;
- rule/config details;
- transfer envelope metadata;
- template schema.

Core searchable relational fields не ховаються в JSON.

- Local SQLite: JSON serialized storage + application schema validation;
- Central PostgreSQL: `jsonb`.

## 11. Boolean

Логічний boolean:

- Local SQLite — INTEGER/boolean adapter з CHECK за потреби;
- Central PostgreSQL — boolean.

## 12. Immutability

Append-only/immutable rules реалізуються насамперед application layer та тестами.

SQLite trigger / PostgreSQL grants+trigger можуть додатково захищати:

- audit;
- closed snapshots;
- finalized document versions;
- completed checks;
- correction evidence;
- central-owned local records від business UPDATE/DELETE.

Не створювати trigger spaghetti для звичайної бізнес-логіки.

## 13. Authority columns/registry

Transferable records повинні мати доступний backend-у authority state без дорогого/неоднозначного inference.

Дозволені реалізації:

- `authority_state`/central version metadata на aggregate root; або
- нормалізована `record_authority` registry.

Остаточний physical choice робиться M1.5 після prototype з урахуванням query simplicity.

Обов’язкова semantics однакова:

`LOCAL → PENDING_APPROVAL → TRANSFERRING → CENTRAL`.

## 14. Index naming

Logical naming convention у migrations:

- `pk_<table>`;
- `uq_<table>_<fields>`;
- `ix_<table>_<fields>`;
- `ck_<table>_<meaning>`;
- `fk_<table>_<field>_<parent>`;
- PostgreSQL-only exclusion: `ex_<table>_<meaning>`.

## 15. SQLite startup pragmas

Local DB initialization обов’язково централізовано задає й перевіряє потрібні pragmas, щонайменше:

- foreign keys enabled;
- journal mode policy, після тестування desktop crash/recovery;
- busy timeout policy;
- synchronous policy, яка не жертвує business durability заради косметичної швидкості.

Конкретні значення затверджуються M1.5 acceptance tests, а не вгадуються архітектурним документом.

## 16. SQLite file access

SQLite database file належить TransportERP-UA application data directory.

Заборонена supported topology:

- один `.db` файл на network share, який напряму відкривають кілька ПК.

Інші робочі місця, якщо local node їх обслуговує, звертаються через application API.

## 17. Central PostgreSQL extensions

Central може використовувати:

- `citext` або normalized application fields;
- `btree_gist` для exclusion constraints;
- `pgcrypto` за фактичною потребою.

Жодне extension не повинно бути required для запуску Local Desktop.

## 18. DB roles / RLS

### Local SQLite
Немає PostgreSQL DB roles/RLS. Authorization — application RBAC + local data authority rules.

### Central PostgreSQL
Можливі migration/runtime/reporting/backup roles та RLS.

## 19. Migrations

Application migrations повинні мати окремо перевірені SQLite і PostgreSQL paths, якщо DDL відрізняється.

CI minimum:

- clean SQLite install;
- SQLite upgrade from previous schema;
- SQLite backup/restore;
- clean central PostgreSQL install;
- PostgreSQL upgrade;
- logical schema/contract parity tests.

Не намагаємося штучно зробити DDL байт-в-байт однаковим між SQLite і PostgreSQL.

## 20. Transfer compatibility

Передача Local → Central відбувається через application/API contract, а не через SQL dump або database replication.

Це дозволяє physical storage типам відрізнятися без зміни бізнес-семантики.
