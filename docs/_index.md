# TransportERP-UA — індекс документації

**Канонічна мова: українська.** Переклади: [English](i18n/en/README.md) · [Español](i18n/es/README.md) · [Français](i18n/fr/README.md) · [Deutsch](i18n/de/README.md)

## 00 — Проєкт
- [Project Charter](00-Project/Project-Charter.md)
- [Roadmap](00-Project/Roadmap.md)
- [Glossary](00-Project/Glossary.md)

## 01 — Архітектура
- [Огляд архітектури](01-Architecture/Architecture-Overview.md)
- [Локалізація](01-Architecture/Localization.md)
- [ADR](01-Architecture/ADR/)
- [Business Rule Catalog](01-Architecture/Business-Rules/Business-Rule-Catalog.md)

## 02 — Дані
- [Модель БД](02-Data/Database-Model.md)
- [DB constraints](02-Data/Database-Constraints.md)
- [Physical Schema v1 — Table Catalog](02-Data/schema/Table-Catalog.md)
- [Physical Schema v1 — ERD](02-Data/schema/ERD-v1.md)
- [Schema conventions](02-Data/schema/00-Conventions.md)
- [Organization & Identity](02-Data/schema/01-Organization-Identity.md)
- [Fleet & Drivers](02-Data/schema/02-Fleet-Drivers.md)
- [Routes, Planning & Trips](02-Data/schema/03-Routes-Planning-Trips.md)
- [Duties & Release](02-Data/schema/04-Duties-Release.md)
- [Waybills, Fuel & Maintenance](02-Data/schema/05-Waybills-Fuel-Maintenance.md)
- [Audit & System](02-Data/schema/06-Audit-System.md)
- [RLS / Immutability / Indexes](02-Data/schema/07-RLS-Immutability-Indexes.md)
- [Foreign Keys & Delete Policy](02-Data/schema/08-Foreign-Keys-and-Delete-Policy.md)
- [Migration Readiness](02-Data/schema/09-Migration-Readiness.md)

## 03 — API
- [OpenAPI MVP Contract](03-API/OpenAPI-MVP-Contract.md)
- [Machine-readable OpenAPI draft](03-API/openapi-mvp-v1.yaml)
- [DTO та schema rules](03-API/DTO-and-Schema-Rules.md)
- [Каталог помилок](03-API/Error-Catalog.md)
- [Permissions Catalog](03-API/Permissions-Catalog.md)
- [Concurrency & Idempotency](03-API/Concurrency-and-Idempotency.md)
- [Transaction Boundaries](03-API/Transaction-Boundaries.md)

## 04 — UX
- [Ролі та робочі простори](04-UX/Roles-and-Workspaces.md)
- [Dispatcher Board](04-UX/Dispatcher-Board.md)
- [Release Workspace](04-UX/Release-Workspace.md)
- [Waybill Workspace](04-UX/Waybill-Workspace.md)
- [Wireframes ролей](04-UX/Role-Wireframes.md)
- [Спільні interaction patterns](04-UX/Interaction-Patterns.md)
- [Навігація та інформаційна архітектура](04-UX/Navigation-and-Information-Architecture.md)

## 06 — Тестування
- [Acceptance Criteria](06-Testing/Acceptance-Criteria.md)
- [Test Strategy](06-Testing/Test-Strategy.md)

## 07 — Експлуатація
- [Deployment](07-Operations/Deployment.md)
- [Backup / DR](07-Operations/Backup-and-DR.md)
- [Observability](07-Operations/Observability.md)

## 08 — MVP / Architecture Freeze
- [MVP Scope](08-MVP/MVP-Scope.md)
- [MVP Definition Package](08-MVP/MVP-Definition-Package.md)
- [Наскрізний робочий день](08-MVP/Operational-Day-Flow.md)
- [Ролі та use cases](08-MVP/Role-Use-Cases.md)
- [Каталог екранів](08-MVP/Screen-Catalog.md)
- [Definition of Done](08-MVP/Definition-of-Done.md)
- [План розробки](08-MVP/Development-Plan.md)

## 10 — Нормативна база
- [Regulatory Register](10-Legal/Regulatory-Register.md)

## 11 — Traceability
- [Traceability Matrix](11-Traceability/Traceability-Matrix.md)

## Мовна політика
- [Правила i18n документації](i18n/README.md)

## Головні checkpoints
- [PROJECT_STATE](../PROJECT_STATE.md)
- [ARCHITECTURE_VERSION](../ARCHITECTURE_VERSION.md)

Документація в цьому каталозі є Obsidian Vault і водночас звичайною Markdown-документацією GitHub.