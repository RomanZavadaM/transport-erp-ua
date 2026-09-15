# Permissions

Backend перевіряє permission, а не лише назву ролі.

Приклади permissions:

- `vehicle.read`, `vehicle.update`;
- `driver.read`, `driver.update`;
- `trip.create`, `trip.cancel`, `trip.close`;
- `duty.vehicle.assign`, `duty.driver.assign`;
- `release.evaluate`, `release.authorize`;
- `technical_check.perform`;
- `medical_check.perform`;
- `waybill.generate`, `waybill.issue`, `waybill.close`, `waybill.correct`;
- `audit.read`.

Administrator не отримує автоматично operational permissions тільки через технічну роль.
