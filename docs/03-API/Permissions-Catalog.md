# Каталог permissions API

Статус: **M0 draft**

Backend перевіряє permissions, а не назву ролі. Ролі є наборами permissions і можуть конфігуруватися в межах затвердженої policy.

## Identity

- `user.read`
- `user.create`
- `user.update`
- `user.status.change`
- `user.roles.manage`
- `role.read`
- `role.manage`
- `permission.read`

## Fleet

- `vehicle.read`
- `vehicle.create`
- `vehicle.update`
- `vehicle.status.change`
- `vehicle_document.read`
- `vehicle_document.manage`
- `odometer.read`
- `odometer.record`
- `odometer.correct`

## Drivers

- `driver.read`
- `driver.read.minimum`
- `driver.create`
- `driver.update`
- `driver.status.change`
- `driver_document.read`
- `driver_document.manage`

## Routes / Planning

- `stop.read`
- `stop.manage`
- `route.read`
- `route.manage`
- `schedule.read`
- `schedule.manage`
- `trip.read`
- `trip.create`
- `trip.cancel`
- `trip.depart`
- `trip.complete`
- `trip.close`
- `trip.event.create`

## Dispatch / Duty

- `duty.read`
- `duty.create`
- `duty.update_plan`
- `duty.vehicle.assign`
- `duty.driver.assign`
- `duty.replace_vehicle`
- `duty.replace_driver`
- `duty.depart`
- `duty.return`
- `duty.close`
- `duty.cancel`

## Release

- `release.read`
- `release.evaluate`
- `release.authorize`
- `medical_check.read`
- `medical_check.perform`
- `medical_check.invalidate`
- `technical_check.read`
- `technical_check.perform`
- `technical_check.invalidate`

## Waybill

- `waybill.read`
- `waybill.create`
- `waybill.generate`
- `waybill.issue`
- `waybill.return`
- `waybill.close`
- `waybill.correct`

## Fuel

- `fuel.read`
- `fuel.record`
- `fuel.reverse`

## Maintenance

- `defect.read`
- `defect.manage`
- `maintenance.read`
- `maintenance.manage`
- `repair.read`
- `repair.manage`

## Reports

- `report.operational.read`
- `report.management.read`
- `report.export`

## Audit

- `audit.read`
- `audit.read.own`
- `audit.export`

## Settings

- `settings.read`
- `settings.manage`
- `template.read`
- `template.manage`
- `numbering.manage`

## Endpoint mapping — критичні commands

| Endpoint | Permission |
|---|---|
| `POST /trips/{id}/cancel` | `trip.cancel` |
| `POST /trips/{id}/depart` | `trip.depart` |
| `POST /trips/{id}/complete` | `trip.complete` |
| `POST /trips/{id}/close` | `trip.close` |
| `POST /duties/{id}/assign-vehicle` | `duty.vehicle.assign` |
| `POST /duties/{id}/assign-driver` | `duty.driver.assign` |
| `POST /duties/{id}/replace-vehicle` | `duty.replace_vehicle` |
| `POST /duties/{id}/replace-driver` | `duty.replace_driver` |
| `POST /duties/{id}/depart` | `duty.depart` |
| `POST /duties/{id}/return` | `duty.return` |
| `POST /duties/{id}/close` | `duty.close` |
| `POST /releases/{id}/evaluate` | `release.evaluate` |
| `POST /releases/{id}/authorize` | `release.authorize` |
| `POST /releases/{id}/medical-checks` | `medical_check.perform` |
| `POST /medical-checks/{id}/invalidate` | `medical_check.invalidate` |
| `POST /releases/{id}/technical-checks` | `technical_check.perform` |
| `POST /technical-checks/{id}/invalidate` | `technical_check.invalidate` |
| `POST /duties/{id}/waybills` | `waybill.create` |
| `POST /waybills/{id}/generate` | `waybill.generate` |
| `POST /waybills/{id}/issue` | `waybill.issue` |
| `POST /waybills/{id}/return` | `waybill.return` |
| `POST /waybills/{id}/close` | `waybill.close` |
| `POST /waybills/{id}/corrections` | `waybill.correct` |

## Projection permissions

Read permission не завжди означає однаковий DTO.

Наприклад:

- `driver.read` → повна operational projection;
- `driver.read.minimum` → ПІБ/ідентифікація/required release fields;
- `audit.read.own` → лише події, що стосуються поточного користувача/дозволеного subject;
- driver mobile/read-only endpoints → own-resource scope.

## Tenant scope

Навіть permission `vehicle.read` не дозволяє читати vehicle іншої company. Tenant isolation застосовується незалежно від RBAC.

## Separation of duties

Permissions повинні дозволяти deployment policy, яка забороняє одній особі одночасно виконувати несумісні критичні функції. Це policy layer поверх permission catalog, а не hardcoded role names.

## Адміністратор

`settings.manage`/`user.roles.manage` не імплікують `release.authorize`, `medical_check.perform` або `technical_check.perform`.

## Правило розвитку

Новий critical endpoint не може бути доданий без:

1. explicit permission;
2. role/policy impact review;
3. API documentation;
4. permission tests;
5. audit decision.