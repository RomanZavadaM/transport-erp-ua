# Модель бази даних

PostgreSQL є транзакційним джерелом істини TransportERP-UA.

Цей файл є оглядовою вхідною сторінкою. Детальна фізична модель M0 знаходиться у [`schema/`](schema/) та зведена в [`schema/Table-Catalog.md`](schema/Table-Catalog.md).

## Physical baseline v1

Фізична модель охоплює **77 основних таблиць** у доменах:

- Organization / Identity;
- Fleet;
- Drivers;
- Routes / Stops;
- Schedules;
- Trips;
- Duty / Dispatch;
- Release / Checks;
- Documents / Waybills / Files;
- Fuel;
- Maintenance / Repairs;
- Corrections;
- Audit / Integration / Operations.

## Ключові принципи

- UUID primary keys, рекомендовано UUIDv7;
- `company_id` як tenant key;
- tenant-aware composite FK для критичних зв'язків;
- `timestamptz` для моментів часу;
- явний `service_date` для operational day;
- normalised operational model;
- versioned routes/schedules/templates;
- plan і fact розділені;
- immutable snapshots/versions для closed history;
- `Trip != Duty`;
- Release належить Duty;
- Waybill базово належить Duty і може містити 1..N Trips;
- audit/events append-only;
- correction workflow замість reopen/silent rewrite.

## Детальна специфікація

- [Конвенції](schema/00-Conventions.md)
- [Organization & Identity](schema/01-Organization-Identity.md)
- [Fleet & Drivers](schema/02-Fleet-Drivers.md)
- [Routes, Planning & Trips](schema/03-Routes-Planning-Trips.md)
- [Duties & Release](schema/04-Duties-Release.md)
- [Waybills, Fuel & Maintenance](schema/05-Waybills-Fuel-Maintenance.md)
- [Audit & System](schema/06-Audit-System.md)
- [RLS, immutability, indexes, partitioning](schema/07-RLS-Immutability-Indexes.md)
- [Foreign keys & delete policy](schema/08-Foreign-Keys-and-Delete-Policy.md)
- [Migration readiness](schema/09-Migration-Readiness.md)
- [Table Catalog](schema/Table-Catalog.md)
- [ERD v1](schema/ERD-v1.md)

## Майбутні домени

GPS, ticketing, payroll, accounting, full warehouse, EDI та external partner API навмисно не входять у physical MVP schema. Ядро залишає для них стабільні integration keys через Vehicle, Driver, Trip, Duty, Waybill та transactional Outbox.