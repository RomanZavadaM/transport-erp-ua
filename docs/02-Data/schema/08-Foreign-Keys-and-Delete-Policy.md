# PostgreSQL Schema — Foreign Keys & Delete Policy

Статус: **M0 physical design draft**

Цей документ є контрольним списком relation policy перед Alembic migration #1.

## 1. Загальне правило

Для business history default:

`ON DELETE RESTRICT` / PostgreSQL `NO ACTION`.

Фізичний cascade застосовується лише до association/configuration rows, втрата яких не стирає бізнес-історію.

## 2. Organization / Identity

| Child | FK | Parent | Delete policy |
|---|---|---|---|
| depots | company_id | companies | RESTRICT |
| company_settings | company_id | companies | RESTRICT |
| users | company_id | companies | RESTRICT |
| user_sessions | user_id/company_id | users | CASCADE допустимий для sessions |
| roles | company_id | companies | RESTRICT |
| user_roles | user_id | users | CASCADE association |
| user_roles | role_id | roles | CASCADE association |
| role_permissions | role_id | roles | CASCADE association |
| role_permissions | permission_id | permissions | RESTRICT/CASCADE association policy |
| api_idempotency_keys | actor_user_id | users | RESTRICT until TTL cleanup |

User business actor не видаляється після історичної активності; status → DISABLED.

## 3. Fleet

| Child | Parent | Delete policy |
|---|---|---|
| vehicles.company/depot | companies/depots | RESTRICT |
| vehicle_status_history.vehicle | vehicles | RESTRICT |
| vehicle_runtime_state.vehicle | vehicles | RESTRICT |
| vehicle_documents.vehicle | vehicles | RESTRICT |
| vehicle_documents.type | vehicle_document_types | RESTRICT |
| vehicle_odometer_readings.vehicle | vehicles | RESTRICT |
| odometer correction_of | vehicle_odometer_readings | RESTRICT |

Document type, який уже використаний, не видаляється — deactivate/archive.

## 4. Drivers

| Child | Parent | Delete policy |
|---|---|---|
| drivers.company/depot | companies/depots | RESTRICT |
| driver_status_history.driver | drivers | RESTRICT |
| driver_documents.driver | drivers | RESTRICT |
| driver_documents.type | driver_document_types | RESTRICT |
| users.driver_id | drivers | SET NULL лише якщо policy explicitly allows unlink before historical use; базово RESTRICT |

Рекомендація MVP: user-driver association змінювати окремою command, а FK використовувати RESTRICT; account disable не видаляє driver.

## 5. Routes / Schedule

| Child | Parent | Delete policy |
|---|---|---|
| route_versions.route | routes | RESTRICT |
| route_stops.route_version | route_versions | RESTRICT |
| route_stops.stop | stops | RESTRICT |
| schedules.route | routes | RESTRICT |
| schedule_versions.schedule | schedules | RESTRICT |
| schedule_versions.route_version | route_versions | RESTRICT |
| schedule_runs.schedule_version | schedule_versions | RESTRICT |
| schedule_runs.service_calendar | service_calendars | RESTRICT |
| schedule_stop_times.schedule_run | schedule_runs | RESTRICT |
| service_calendar_exceptions.calendar | service_calendars | RESTRICT |

Draft-only child cleanup може виконувати application explicit delete до activation/usage, але production migration FK лишається restrictive; application перевіряє “unused draft” перед delete.

## 6. Trips

| Child | Parent | Delete policy |
|---|---|---|
| trips.schedule_run | schedule_runs | RESTRICT |
| trips.route_version | route_versions | RESTRICT |
| trip_stop_plan.trip | trips | RESTRICT |
| trip_stop_plan.stop | stops | RESTRICT |
| trip_actuals.trip | trips | RESTRICT |
| trip_stop_actuals.trip | trips | RESTRICT |
| trip_actual_snapshots.trip | trips | RESTRICT |
| trip_actual_snapshots.previous | trip_actual_snapshots | RESTRICT |
| trip_events.trip | trips | RESTRICT |

`trips.effective_actual_snapshot_id` → snapshot: RESTRICT/NO ACTION; deletion snapshot заборонена anyway.

## 7. Duties / Assignments

| Child | Parent | Delete policy |
|---|---|---|
| duties.depot | depots | RESTRICT |
| duty_trips.duty | duties | RESTRICT |
| duty_trips.trip | trips | RESTRICT |
| vehicle assignments.duty | duties | RESTRICT |
| vehicle assignments.vehicle | vehicles | RESTRICT |
| driver assignments.duty | duties | RESTRICT |
| driver assignments.driver | drivers | RESTRICT |
| vehicle usage.duty/vehicle | duties/vehicles | RESTRICT |
| driver usage.duty/driver | duties/drivers | RESTRICT |
| duty_events.duty | duties | RESTRICT |

Assignment cancellation/removal = business status, не DELETE.

## 8. Release / Checks

| Child | Parent | Delete policy |
|---|---|---|
| releases.duty | duties | RESTRICT |
| pre_trip_checks.release | releases | RESTRICT |
| pre_trip_checks.template | check_templates | RESTRICT |
| medical detail.check | pre_trip_checks | RESTRICT |
| medical detail.driver | drivers | RESTRICT |
| technical detail.check | pre_trip_checks | RESTRICT |
| technical detail.vehicle | vehicles | RESTRICT |
| check_results.check | pre_trip_checks | RESTRICT |
| check_results.template_item | check_template_items | RESTRICT |
| check invalidation.check | pre_trip_checks | RESTRICT |
| check invalidation.replacement | pre_trip_checks | RESTRICT |
| release evaluations.release | releases | RESTRICT |
| release evaluations.rule | compliance_rules | RESTRICT or nullable historical snapshot code |
| release authorizations.release | releases | RESTRICT |

Check template items можуть CASCADE з draft template лише до use; після template activation/use deletion не дозволяється application policy.

## 9. Waybills / Files

| Child | Parent | Delete policy |
|---|---|---|
| waybills.duty | duties | RESTRICT |
| waybill_trips.waybill | waybills | RESTRICT |
| waybill_trips.trip | trips | RESTRICT |
| waybill_versions.waybill | waybills | RESTRICT |
| waybill_versions.template_version | document_template_versions | RESTRICT |
| waybill_versions.pdf_file | files | RESTRICT |
| waybill_versions.previous | waybill_versions | RESTRICT |
| waybill_versions.correction | correction_cases | RESTRICT |
| waybills.current_version | waybill_versions | RESTRICT |
| entity_attachments.file | files | RESTRICT |

File metadata referenced by closed document cannot be deleted by application cleanup. Orphan file garbage collection operates only on files with no references and adequate grace period.

## 10. Fuel

All refs from `fuel_operations` to vehicle/duty/trip/waybill/fuel_type are RESTRICT.

`reversal_of_id` is RESTRICT.

Business correction never deletes source fuel row.

## 11. Maintenance / Repair

All vehicle refs: RESTRICT.

- defects technical_check reference RESTRICT;
- maintenance events → plan RESTRICT;
- repair items → repair order: CASCADE може бути допустимий **лише для never-started draft repair**, але простіше і безпечніше MVP — RESTRICT + application batch cleanup before any history. Після OPEN/history — no delete.

## 12. Corrections

Correction case references entity polymorphically and не має universal FK. Version/snapshot child records мають прямий FK на correction case RESTRICT.

Correction case після створення не видаляється; може бути CANCELLED/REJECTED.

## 13. Audit / Outbox / Reports

- `audit_log.actor_user_id` → users: RESTRICT або nullable historical identity strategy. MVP recommendation: RESTRICT, user never physically deleted.
- outbox aggregate refs polymorphic — no universal FK.
- report_exports.requested_by → users RESTRICT;
- report_exports.file_id → files RESTRICT.

## 14. Why not SET NULL widely

`ON DELETE SET NULL` у бізнес-історії приховує, що parent було фізично видалено. Оскільки parent history і так не повинна видалятися, default RESTRICT є яснішим і безпечнішим.

## 15. Why not CASCADE widely

Cascade з `vehicle` на documents/odometer/trips або з `duty` на assignments/checks/waybill може одним DELETE знищити юридично/фінансово значиму історію. Така схема заборонена.

## 16. Physical delete API

Для основних production entities `DELETE /...` endpoint не передбачається.

Reference/draft cleanup, де справді потрібен фізичний delete, має:

- окремий explicit endpoint/command;
- guard `never used`;
- permission;
- audit;
- DB FK як останню лінію захисту.
