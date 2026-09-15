# TransportERP-UA — індекс документації

**Канонічна мова: українська.** Переклади: [English](i18n/en/README.md) · [Español](i18n/es/README.md) · [Français](i18n/fr/README.md) · [Deutsch](i18n/de/README.md)

## Найважливіше зараз

- [PROJECT_STATE](../PROJECT_STATE.md)
- [ARCHITECTURE_VERSION](../ARCHITECTURE_VERSION.md)
- [ADR-0007 — Local Desktop / SQLite / Central Transfer](01-Architecture/ADR/ADR-0007-Local-SQLite-and-Central-Transfer.md)
- [Огляд архітектури](01-Architecture/Architecture-Overview.md)
- [Модель БД Local SQLite + Central PostgreSQL](02-Data/Database-Model.md)
- [Deployment profiles](07-Operations/Deployment.md)
- [Backup / Restore](07-Operations/Backup-and-DR.md)

## 00 — Проєкт
- [Project Charter](00-Project/Project-Charter.md)
- [Roadmap](00-Project/Roadmap.md)
- [Glossary](00-Project/Glossary.md)

## 01 — Архітектура
- [Огляд архітектури](01-Architecture/Architecture-Overview.md)
- [ADR](01-Architecture/ADR/)
- [Локалізація](01-Architecture/Localization.md)
- [Business Rules](01-Architecture/Business-Rules/README.md)

## 02 — Дані
- [Модель БД](02-Data/Database-Model.md)
- [DB constraints](02-Data/Database-Constraints.md)
- [Schema conventions Local/Central](02-Data/schema/00-Conventions.md)
- [Organization & Identity](02-Data/schema/01-Organization-Identity.md)
- [Fleet & Drivers](02-Data/schema/02-Fleet-Drivers.md)
- [Routes, Planning & Trips](02-Data/schema/03-Routes-Planning-Trips.md)
- [Duties & Release](02-Data/schema/04-Duties-Release.md)
- [Waybills, Fuel & Maintenance](02-Data/schema/05-Waybills-Fuel-Maintenance.md)
- [Audit / Transfer / Integrity](02-Data/schema/06-Audit-System.md)
- [SQLite/PostgreSQL integrity rules](02-Data/schema/07-RLS-Immutability-Indexes.md)
- [Foreign Keys & Delete Policy](02-Data/schema/08-Foreign-Keys-and-Delete-Policy.md)
- [Migration Readiness](02-Data/schema/09-Migration-Readiness.md)
- [Table Catalog](02-Data/schema/Table-Catalog.md)
- [ERD v1](02-Data/schema/ERD-v1.md)

> Detailed schema files 01–05 походять з PostgreSQL-oriented v1.5 physical design і в v1.6 трактуються як доменно-структурна база, яку M1.5 адаптує до SQLite local profile. PostgreSQL-specific DDL не є local requirement.

## 03 — API
- [OpenAPI MVP Contract](03-API/OpenAPI-MVP-Contract.md)
- [Machine-readable OpenAPI](03-API/openapi-mvp-v1.yaml)
- [DTO та schema rules](03-API/DTO-and-Schema-Rules.md)
- [Каталог помилок](03-API/Error-Catalog.md)
- [Permissions Catalog](03-API/Permissions-Catalog.md)
- [Concurrency & Idempotency](03-API/Concurrency-and-Idempotency.md)
- [Transaction Boundaries + Transfer flow](03-API/Transaction-Boundaries.md)

## 04 — UX
- [Ролі та робочі простори](04-UX/Roles-and-Workspaces.md)
- [Dispatcher Board](04-UX/Dispatcher-Board.md)
- [Release Workspace](04-UX/Release-Workspace.md)
- [Waybill Workspace](04-UX/Waybill-Workspace.md)
- [Wireframes ролей](04-UX/Role-Wireframes.md)
- [Interaction patterns](04-UX/Interaction-Patterns.md)
- [Навігація](04-UX/Navigation-and-Information-Architecture.md)

## 06 — Тестування
- [Acceptance Criteria](06-Testing/Acceptance-Criteria.md)
- [Test Strategy](06-Testing/Test-Strategy.md)

## 07 — Експлуатація
- [Deployment](07-Operations/Deployment.md)
- [Backup / DR](07-Operations/Backup-and-DR.md)
- [Observability](07-Operations/Observability.md)
- [Integrity Checker](07-Operations/Integrity-Checker.md)

## 08 — MVP
- [MVP Scope](08-MVP/MVP-Scope.md)
- [MVP Definition Package](08-MVP/MVP-Definition-Package.md)
- [Operational Day Flow](08-MVP/Operational-Day-Flow.md)
- [Role Use Cases](08-MVP/Role-Use-Cases.md)
- [Screen Catalog](08-MVP/Screen-Catalog.md)
- [Definition of Done](08-MVP/Definition-of-Done.md)
- [Development Plan](08-MVP/Development-Plan.md)

## 10 — Нормативна база
- [Regulatory Register](10-Legal/Regulatory-Register.md)

## 11 — Traceability
- [Traceability Matrix](11-Traceability/Traceability-Matrix.md)

## Мовна політика
- [Правила i18n документації](i18n/README.md)

Документація в цьому каталозі є Obsidian Vault і звичайною Markdown-документацією GitHub.
