# PostgreSQL Physical Schema v1 — Каталог таблиць

Статус: **M0 physical design draft**

Цей каталог є зведеним індексом фізичної моделі. Детальні поля/constraints описані у модульних файлах `schema/`.

## Організація та Identity

| Таблиця | Призначення |
|---|---|
| `companies` | підприємства / tenant root |
| `company_settings` | рідкі конфігураційні параметри |
| `depots` | депо / майданчики |
| `users` | користувачі |
| `user_sessions` | secure sessions/refresh lifecycle |
| `roles` | ролі |
| `permissions` | стабільні technical permissions |
| `user_roles` | призначення ролей користувачам |
| `role_permissions` | permissions ролей |
| `api_idempotency_keys` | захист repeat critical requests |

## Fleet

| Таблиця | Призначення |
|---|---|
| `vehicle_types` | типи транспортних засобів |
| `fuel_types` | типи пального |
| `vehicles` | автобуси |
| `vehicle_status_history` | історія lifecycle статусів |
| `vehicle_runtime_state` | rebuildable current-state projection |
| `vehicle_document_types` | типи документів автобуса |
| `vehicle_documents` | документи автобуса |
| `vehicle_odometer_readings` | історія показників одометра |

## Drivers

| Таблиця | Призначення |
|---|---|
| `drivers` | водії |
| `driver_status_history` | історія employment/lifecycle status |
| `driver_document_types` | типи документів водія |
| `driver_documents` | документи водія |

## Routes & Stops

| Таблиця | Призначення |
|---|---|
| `stops` | зупинки |
| `routes` | стабільна сутність маршруту |
| `route_versions` | версії структури маршруту |
| `route_stops` | послідовність зупинок у версії |

## Schedules

| Таблиця | Призначення |
|---|---|
| `schedules` | стабільна сутність розкладу |
| `schedule_versions` | версії розкладу |
| `service_calendars` | календарі днів роботи |
| `service_calendar_exceptions` | винятки ADD/REMOVE |
| `schedule_runs` | регулярні відправлення |
| `schedule_stop_times` | offsets часу по зупинках |

## Trips

| Таблиця | Призначення |
|---|---|
| `trips` | конкретні рейси на service date |
| `trip_stop_plan` | snapshot планових зупинок |
| `trip_actuals` | mutable факти до close |
| `trip_stop_actuals` | фактичні зупинки |
| `trip_actual_snapshots` | immutable closed/corrected facts |
| `trip_events` | append-only timeline рейсу |

## Duties / Dispatch

| Таблиця | Призначення |
|---|---|
| `duties` | наряди / operational shifts |
| `duty_trips` | рейси наряду |
| `duty_vehicle_assignments` | планові призначення автобусів |
| `duty_driver_assignments` | планові призначення водіїв |
| `duty_vehicle_usage` | фактичне використання автобусів |
| `duty_driver_usage` | фактична робота водіїв |
| `duty_events` | append-only timeline Duty |

## Release / Checks

| Таблиця | Призначення |
|---|---|
| `releases` | workflow випуску Duty |
| `check_templates` | versioned checklists |
| `check_template_items` | пункти checklist |
| `pre_trip_checks` | передрейсові перевірки |
| `medical_check_details` | мінімальний медичний результат |
| `technical_check_details` | технічний результат |
| `check_results` | результати checklist items |
| `pre_trip_check_invalidations` | invalidation completed check |
| `compliance_rules` | versioned release rules |
| `release_rule_evaluations` | append-only evaluation batches |
| `release_authorizations` | рішення диспетчера |

## Documents / Waybills

| Таблиця | Призначення |
|---|---|
| `number_sequences` | атомарна нумерація документів |
| `document_templates` | тип/ідентичність шаблону |
| `document_template_versions` | version + locale HTML/CSS schema |
| `waybills` | aggregate шляхового листа |
| `waybill_trips` | рейси, включені в лист |
| `waybill_versions` | immutable snapshot/PDF history |
| `files` | metadata object storage |
| `entity_attachments` | generic вкладення |

## Fuel

| Таблиця | Призначення |
|---|---|
| `fuel_operations` | ledger-like журнал паливних операцій |

## Maintenance / Repairs

| Таблиця | Призначення |
|---|---|
| `defects` | дефекти автобуса |
| `maintenance_types` | типи ТО |
| `maintenance_plans` | плани ТО |
| `maintenance_events` | факти ТО |
| `repair_orders` | ремонтні наряди |
| `repair_order_items` | роботи/частини ремонту |

## Corrections

| Таблиця | Призначення |
|---|---|
| `correction_cases` | контрольований workflow виправлення closed history |

## Audit / Integration / Operations

| Таблиця | Призначення |
|---|---|
| `audit_log` | canonical append-only audit |
| `audit_partition_seals` | evidence integrity seal |
| `outbox_events` | transactional integration outbox |
| `report_exports` | asynchronous report artifacts |
| `system_integrity_alerts` | виявлені consistency problems |

## Кількість

Physical baseline містить **57 основних таблиць** без майбутніх projection/materialized views та без optional technical `background_jobs`/`security_events`.

Кількість не є ціллю сама по собі. Таблиці виділені там, де потрібні окремі:

- state/lifecycle;
- FK/constraints;
- history/immutability;
- security policy;
- query pattern.

## Не створюються в MVP

Навмисно відсутні таблиці доменів:

- GPS positions/tracks/devices;
- ticketing/passenger accounting;
- payroll;
- accounting ledger;
- full parts warehouse;
- external partner API credentials/mappings;
- electronic signature/EDI workflow.

Для них залишені стабільні точки інтеграції (`vehicle`, `driver`, `trip`, `duty`, `waybill`, `outbox`).

## Джерела детального design

- [00 — Conventions](00-Conventions.md)
- [01 — Organization & Identity](01-Organization-Identity.md)
- [02 — Fleet & Drivers](02-Fleet-Drivers.md)
- [03 — Routes, Planning & Trips](03-Routes-Planning-Trips.md)
- [04 — Duties & Release](04-Duties-Release.md)
- [05 — Waybills, Fuel & Maintenance](05-Waybills-Fuel-Maintenance.md)
- [06 — Audit & System](06-Audit-System.md)
- [07 — RLS / Immutability / Indexes](07-RLS-Immutability-Indexes.md)
- [08 — FK & Delete Policy](08-Foreign-Keys-and-Delete-Policy.md)
- [ERD v1](ERD-v1.md)
