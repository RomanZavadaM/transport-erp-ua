# Модель бази даних

TransportERP-UA має **одну логічну бізнес-модель** і два physical profiles:

- **Local SQLite** — базова operational БД desktop-застосунку;
- **Central PostgreSQL** — БД вищого/серверного рівня.

PostgreSQL більше не є обов’язковим для локальної роботи.

## Logical baseline

Модель охоплює домени:

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
- Audit;
- Transfer / Central authority;
- Operations.

Існуючий M0 catalog приблизно на 77 таблиць залишається джерелом доменної структури, але PostgreSQL-specific DDL більше не вважається єдиною physical реалізацією.

## Спільні принципи

- UUID identifiers генеруються application-side;
- `company_id` зберігається там, де потрібен enterprise context/central consolidation;
- Plan і Fact розділені;
- `Trip != Duty`;
- Release належить Duty;
- Waybill пов'язаний з Duty і 1..N Trips;
- CLOSED history immutable;
- correction workflow замість silent rewrite;
- audit append-only;
- optimistic `row_version` для mutable aggregates;
- критичні business rules реалізуються в backend, а БД їх підсилює доступними constraints.

## Local SQLite profile

Local schema повинна працювати без PostgreSQL extensions.

Використовуються portable concepts:

- FK;
- UNIQUE;
- CHECK;
- indexes;
- transactions;
- triggers лише для фундаментальних invariants;
- application-side UUID;
- JSON serialization для extensible payloads;
- authority/transfer tables з architecture-v1.6.

RLS, GiST, `tstzrange`, PostgreSQL DB roles та partitioning не є local dependencies.

## Central PostgreSQL profile

Central може використовувати PostgreSQL-specific defense-in-depth:

- RLS;
- composite tenant-aware FK;
- range/exclusion constraints;
- row locking;
- server roles;
- partitioning;
- JSONB indexes після profiling.

## Authority model

До central ACK business data мають local authority.

Після ACK передані records локально read-only; central стає місцем подальшої модифікації цих records.

Деталі: `ADR-0007-Local-SQLite-and-Central-Transfer.md` та `schema/06-Audit-System.md`.

## Physical specification

- [Конвенції Local/Central](schema/00-Conventions.md)
- [Organization & Identity](schema/01-Organization-Identity.md)
- [Fleet & Drivers](schema/02-Fleet-Drivers.md)
- [Routes, Planning & Trips](schema/03-Routes-Planning-Trips.md)
- [Duties & Release](schema/04-Duties-Release.md)
- [Waybills, Fuel & Maintenance](schema/05-Waybills-Fuel-Maintenance.md)
- [Audit & Transfer](schema/06-Audit-System.md)
- [SQLite/PostgreSQL integrity](schema/07-RLS-Immutability-Indexes.md)
- [Foreign keys & delete policy](schema/08-Foreign-Keys-and-Delete-Policy.md)
- [Migration readiness](schema/09-Migration-Readiness.md)
- [Table Catalog](schema/Table-Catalog.md)
- [ERD v1](schema/ERD-v1.md)

## Практичне правило для подальшої розробки

Кожна нова таблиця/constraint проходить дві перевірки:

1. як це працює на Local SQLite;
2. які додаткові гарантії доречні на Central PostgreSQL.

Не приймаємо business design, який випадково робить локальний desktop залежним від PostgreSQL feature.
