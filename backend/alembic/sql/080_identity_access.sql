CREATE OR REPLACE FUNCTION auth_resolve_company_id(p_edrpou text)
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT id
    FROM companies
    WHERE edrpou = p_edrpou
      AND status = 'ACTIVE'
    LIMIT 1
$$;

CREATE OR REPLACE FUNCTION enforce_user_role_tenant()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    role_company uuid;
BEGIN
    SELECT company_id INTO role_company
    FROM roles
    WHERE id = NEW.role_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'role is not visible for assignment'
            USING ERRCODE = '23503';
    END IF;

    IF role_company IS NOT NULL AND role_company <> NEW.company_id THEN
        RAISE EXCEPTION 'cross-tenant role assignment is not allowed'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_user_roles_tenant_guard
    BEFORE INSERT OR UPDATE ON user_roles
    FOR EACH ROW EXECUTE FUNCTION enforce_user_role_tenant();

INSERT INTO permissions (code, description, domain) VALUES
('user.read','Read users','identity'),
('user.create','Create users','identity'),
('user.update','Update users','identity'),
('user.status.change','Change user status','identity'),
('user.roles.manage','Manage user roles','identity'),
('role.read','Read roles','identity'),
('role.manage','Manage roles','identity'),
('permission.read','Read permissions','identity'),
('vehicle.read','Read vehicles','fleet'),
('vehicle.create','Create vehicles','fleet'),
('vehicle.update','Update vehicles','fleet'),
('vehicle.status.change','Change vehicle status','fleet'),
('vehicle_document.read','Read vehicle documents','fleet'),
('vehicle_document.manage','Manage vehicle documents','fleet'),
('odometer.read','Read odometer','fleet'),
('odometer.record','Record odometer','fleet'),
('odometer.correct','Correct odometer','fleet'),
('driver.read','Read drivers','drivers'),
('driver.read.minimum','Read minimum driver projection','drivers'),
('driver.create','Create drivers','drivers'),
('driver.update','Update drivers','drivers'),
('driver.status.change','Change driver status','drivers'),
('driver_document.read','Read driver documents','drivers'),
('driver_document.manage','Manage driver documents','drivers'),
('stop.read','Read stops','planning'),
('stop.manage','Manage stops','planning'),
('route.read','Read routes','planning'),
('route.manage','Manage routes','planning'),
('schedule.read','Read schedules','planning'),
('schedule.manage','Manage schedules','planning'),
('trip.read','Read trips','trips'),
('trip.create','Create trips','trips'),
('trip.cancel','Cancel trips','trips'),
('trip.depart','Depart trips','trips'),
('trip.complete','Complete trips','trips'),
('trip.close','Close trips','trips'),
('trip.event.create','Create trip events','trips'),
('duty.read','Read duties','dispatch'),
('duty.create','Create duties','dispatch'),
('duty.update_plan','Update duty plan','dispatch'),
('duty.vehicle.assign','Assign vehicle','dispatch'),
('duty.driver.assign','Assign driver','dispatch'),
('duty.replace_vehicle','Replace vehicle','dispatch'),
('duty.replace_driver','Replace driver','dispatch'),
('duty.depart','Depart duty','dispatch'),
('duty.return','Return duty','dispatch'),
('duty.close','Close duty','dispatch'),
('duty.cancel','Cancel duty','dispatch'),
('release.read','Read release','release'),
('release.evaluate','Evaluate release','release'),
('release.authorize','Authorize release','release'),
('medical_check.read','Read medical checks','release'),
('medical_check.perform','Perform medical check','release'),
('medical_check.invalidate','Invalidate medical check','release'),
('technical_check.read','Read technical checks','release'),
('technical_check.perform','Perform technical check','release'),
('technical_check.invalidate','Invalidate technical check','release'),
('driver_predeparture_check.read','Read driver predeparture checks','release'),
('driver_predeparture_check.perform','Perform driver predeparture check','release'),
('driver_predeparture_check.invalidate','Invalidate driver predeparture check','release'),
('waybill.read','Read waybills','waybill'),
('waybill.create','Create waybills','waybill'),
('waybill.generate','Generate waybills','waybill'),
('waybill.issue','Issue waybills','waybill'),
('waybill.return','Return waybills','waybill'),
('waybill.close','Close waybills','waybill'),
('waybill.correct','Correct waybills','waybill'),
('fuel.read','Read fuel operations','fuel'),
('fuel.record','Record fuel operations','fuel'),
('fuel.reverse','Reverse fuel operations','fuel'),
('defect.read','Read defects','maintenance'),
('defect.manage','Manage defects','maintenance'),
('maintenance.read','Read maintenance','maintenance'),
('maintenance.manage','Manage maintenance','maintenance'),
('repair.read','Read repairs','maintenance'),
('repair.manage','Manage repairs','maintenance'),
('report.operational.read','Read operational reports','reports'),
('report.management.read','Read management reports','reports'),
('report.export','Export reports','reports'),
('audit.read','Read audit','audit'),
('audit.read.own','Read own audit','audit'),
('audit.export','Export audit','audit'),
('settings.read','Read settings','settings'),
('settings.manage','Manage settings','settings'),
('template.read','Read templates','settings'),
('template.manage','Manage templates','settings'),
('numbering.manage','Manage numbering','settings')
ON CONFLICT (code) DO UPDATE
SET description = EXCLUDED.description,
    domain = EXCLUDED.domain;

INSERT INTO roles (company_id, code, name, system_role, active)
SELECT NULL, 'ADMIN', 'Адміністратор', true, true
WHERE NOT EXISTS (
    SELECT 1 FROM roles WHERE company_id IS NULL AND code = 'ADMIN'
);

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.code IN (
    'user.read','user.create','user.update','user.status.change','user.roles.manage',
    'role.read','role.manage','permission.read',
    'settings.read','settings.manage','template.read','template.manage','numbering.manage',
    'audit.read','audit.export'
)
WHERE r.company_id IS NULL AND r.code = 'ADMIN'
ON CONFLICT DO NOTHING;
