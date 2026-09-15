DROP TRIGGER IF EXISTS trg_user_roles_tenant_guard ON user_roles;
DROP FUNCTION IF EXISTS enforce_user_role_tenant();
DROP FUNCTION IF EXISTS auth_resolve_company_id(text);

DELETE FROM roles
WHERE company_id IS NULL AND code = 'ADMIN' AND system_role = true;

DELETE FROM permissions
WHERE code IN (
'user.read','user.create','user.update','user.status.change','user.roles.manage',
'role.read','role.manage','permission.read',
'vehicle.read','vehicle.create','vehicle.update','vehicle.status.change',
'vehicle_document.read','vehicle_document.manage','odometer.read','odometer.record','odometer.correct',
'driver.read','driver.read.minimum','driver.create','driver.update','driver.status.change',
'driver_document.read','driver_document.manage',
'stop.read','stop.manage','route.read','route.manage','schedule.read','schedule.manage',
'trip.read','trip.create','trip.cancel','trip.depart','trip.complete','trip.close','trip.event.create',
'duty.read','duty.create','duty.update_plan','duty.vehicle.assign','duty.driver.assign',
'duty.replace_vehicle','duty.replace_driver','duty.depart','duty.return','duty.close','duty.cancel',
'release.read','release.evaluate','release.authorize',
'medical_check.read','medical_check.perform','medical_check.invalidate',
'technical_check.read','technical_check.perform','technical_check.invalidate',
'driver_predeparture_check.read','driver_predeparture_check.perform','driver_predeparture_check.invalidate',
'waybill.read','waybill.create','waybill.generate','waybill.issue','waybill.return','waybill.close','waybill.correct',
'fuel.read','fuel.record','fuel.reverse',
'defect.read','defect.manage','maintenance.read','maintenance.manage','repair.read','repair.manage',
'report.operational.read','report.management.read','report.export',
'audit.read','audit.read.own','audit.export',
'settings.read','settings.manage','template.read','template.manage','numbering.manage'
);
