CREATE TABLE vehicle_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(50) NOT NULL,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true
);
CREATE UNIQUE INDEX ux_vehicle_types_tenant_code
    ON vehicle_types(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_vehicle_types_system_code
    ON vehicle_types(code) WHERE company_id IS NULL;

CREATE TABLE fuel_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(30) NOT NULL,
    name text NOT NULL,
    unit varchar(10) NOT NULL DEFAULT 'L',
    active boolean NOT NULL DEFAULT true
);
CREATE UNIQUE INDEX ux_fuel_types_tenant_code
    ON fuel_types(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_fuel_types_system_code
    ON fuel_types(code) WHERE company_id IS NULL;

CREATE TABLE vehicles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    depot_id uuid NULL,
    fleet_number varchar(30) NOT NULL,
    registration_number varchar(20) NOT NULL,
    vin varchar(32) NULL,
    make varchar(80) NOT NULL,
    model varchar(80) NOT NULL,
    year smallint NULL,
    vehicle_type_id uuid NULL REFERENCES vehicle_types(id) ON DELETE RESTRICT,
    fuel_type_id uuid NULL REFERENCES fuel_types(id) ON DELETE RESTRICT,
    seats smallint NULL,
    capacity_total smallint NULL,
    lifecycle_status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    commissioned_at date NULL,
    decommissioned_at date NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_vehicles_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_vehicles_fleet_number UNIQUE (company_id, fleet_number),
    CONSTRAINT uq_vehicles_registration UNIQUE (company_id, registration_number),
    CONSTRAINT fk_vehicles_depot FOREIGN KEY (company_id, depot_id)
        REFERENCES depots(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_vehicles_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_vehicles_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_vehicles_status CHECK (
        lifecycle_status IN ('ACTIVE','SUSPENDED','REPAIR','DECOMMISSIONED')
    ),
    CONSTRAINT ck_vehicles_year CHECK (year IS NULL OR year BETWEEN 1950 AND 2100),
    CONSTRAINT ck_vehicles_seats CHECK (seats IS NULL OR seats >= 0),
    CONSTRAINT ck_vehicles_capacity CHECK (capacity_total IS NULL OR capacity_total >= 0),
    CONSTRAINT ck_vehicles_capacity_seats CHECK (
        seats IS NULL OR capacity_total IS NULL OR capacity_total >= seats
    ),
    CONSTRAINT ck_vehicles_commission_dates CHECK (
        decommissioned_at IS NULL OR commissioned_at IS NULL
        OR decommissioned_at >= commissioned_at
    )
);
CREATE UNIQUE INDEX ux_vehicles_vin ON vehicles(vin) WHERE vin IS NOT NULL;
CREATE INDEX ix_vehicles_company_status ON vehicles(company_id, lifecycle_status);
CREATE INDEX ix_vehicles_depot_status ON vehicles(company_id, depot_id, lifecycle_status);

CREATE TABLE vehicle_status_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    status varchar(30) NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    reason_code varchar(80) NULL,
    reason text NULL,
    changed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_vehicle_status_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_vehicle_status_actor FOREIGN KEY (company_id, changed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_vehicle_status_period CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT ck_vehicle_status_value CHECK (
        status IN ('ACTIVE','SUSPENDED','REPAIR','DECOMMISSIONED')
    )
);
CREATE UNIQUE INDEX ux_vehicle_status_open_period
    ON vehicle_status_history(vehicle_id) WHERE valid_to IS NULL;
CREATE INDEX ix_vehicle_status_timeline ON vehicle_status_history(vehicle_id, valid_from DESC);

CREATE TABLE vehicle_runtime_state (
    vehicle_id uuid PRIMARY KEY REFERENCES vehicles(id) ON DELETE RESTRICT,
    company_id uuid NOT NULL,
    last_confirmed_odometer_km bigint NULL,
    last_odometer_at timestamptz NULL,
    current_duty_id uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_vehicle_runtime_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_vehicle_runtime_odometer CHECK (
        last_confirmed_odometer_km IS NULL OR last_confirmed_odometer_km >= 0
    )
);

CREATE TABLE vehicle_document_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(80) NOT NULL,
    name text NOT NULL,
    required_for_release boolean NOT NULL DEFAULT false,
    blocks_release_if_expired boolean NOT NULL DEFAULT false,
    warning_days integer NULL,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT ck_vehicle_document_type_warning CHECK (warning_days IS NULL OR warning_days >= 0)
);
CREATE UNIQUE INDEX ux_vehicle_document_types_tenant_code
    ON vehicle_document_types(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_vehicle_document_types_system_code
    ON vehicle_document_types(code) WHERE company_id IS NULL;

CREATE TABLE vehicle_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    document_type_id uuid NOT NULL REFERENCES vehicle_document_types(id) ON DELETE RESTRICT,
    series varchar(30) NULL,
    number varchar(100) NOT NULL,
    issued_at date NULL,
    valid_from date NULL,
    valid_until date NULL,
    issuer text NULL,
    status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    file_id uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT fk_vehicle_documents_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_vehicle_documents_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_vehicle_documents_dates CHECK (
        valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from
    ),
    CONSTRAINT ck_vehicle_documents_status CHECK (status IN ('ACTIVE','REVOKED','SUPERSEDED'))
);
CREATE INDEX ix_vehicle_documents_type
    ON vehicle_documents(company_id, vehicle_id, document_type_id);
CREATE INDEX ix_vehicle_documents_expiry ON vehicle_documents(company_id, valid_until);
CREATE INDEX ix_vehicle_documents_active_expiry
    ON vehicle_documents(vehicle_id, document_type_id, valid_until) WHERE status = 'ACTIVE';

CREATE TABLE vehicle_odometer_readings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    recorded_at timestamptz NOT NULL,
    odometer_km bigint NOT NULL,
    confirmed boolean NOT NULL DEFAULT true,
    source varchar(30) NOT NULL,
    trip_id uuid NULL,
    duty_id uuid NULL,
    waybill_id uuid NULL,
    correction_of_id uuid NULL REFERENCES vehicle_odometer_readings(id) ON DELETE RESTRICT,
    recorded_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_odometer_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_odometer_actor FOREIGN KEY (company_id, recorded_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_odometer_nonnegative CHECK (odometer_km >= 0),
    CONSTRAINT ck_odometer_source CHECK (
        source IN ('MANUAL','WAYBILL','TRIP','TECH_CHECK','GPS','IMPORT','CORRECTION')
    )
);
CREATE INDEX ix_odometer_vehicle_time
    ON vehicle_odometer_readings(company_id, vehicle_id, recorded_at DESC);
CREATE INDEX ix_odometer_confirmed
    ON vehicle_odometer_readings(vehicle_id, recorded_at DESC) WHERE confirmed = true;

CREATE TABLE drivers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    default_depot_id uuid NULL,
    personnel_number varchar(30) NOT NULL,
    last_name varchar(100) NOT NULL,
    first_name varchar(100) NOT NULL,
    middle_name varchar(100) NULL,
    birth_date date NULL,
    phone varchar(40) NULL,
    employment_status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    hire_date date NULL,
    dismissal_date date NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_drivers_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_drivers_personnel UNIQUE (company_id, personnel_number),
    CONSTRAINT fk_drivers_depot FOREIGN KEY (company_id, default_depot_id)
        REFERENCES depots(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_drivers_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_drivers_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_drivers_status CHECK (
        employment_status IN ('ACTIVE','LEAVE','SICK','SUSPENDED','TERMINATED')
    ),
    CONSTRAINT ck_drivers_dates CHECK (
        dismissal_date IS NULL OR hire_date IS NULL OR dismissal_date >= hire_date
    )
);
CREATE INDEX ix_drivers_company_status ON drivers(company_id, employment_status);
CREATE INDEX ix_drivers_depot_status ON drivers(company_id, default_depot_id, employment_status);

CREATE TABLE driver_status_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    status varchar(30) NOT NULL,
    valid_from timestamptz NOT NULL,
    valid_to timestamptz NULL,
    reason_code varchar(80) NULL,
    reason text NULL,
    changed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_driver_status_driver FOREIGN KEY (company_id, driver_id)
        REFERENCES drivers(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_driver_status_actor FOREIGN KEY (company_id, changed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_driver_status_period CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT ck_driver_status_value CHECK (
        status IN ('ACTIVE','LEAVE','SICK','SUSPENDED','TERMINATED')
    )
);
CREATE UNIQUE INDEX ux_driver_status_open_period
    ON driver_status_history(driver_id) WHERE valid_to IS NULL;
CREATE INDEX ix_driver_status_timeline ON driver_status_history(driver_id, valid_from DESC);

CREATE TABLE driver_document_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(80) NOT NULL,
    name text NOT NULL,
    required_for_release boolean NOT NULL DEFAULT false,
    blocks_release_if_expired boolean NOT NULL DEFAULT false,
    warning_days integer NULL,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT ck_driver_document_type_warning CHECK (warning_days IS NULL OR warning_days >= 0)
);
CREATE UNIQUE INDEX ux_driver_document_types_tenant_code
    ON driver_document_types(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_driver_document_types_system_code
    ON driver_document_types(code) WHERE company_id IS NULL;

CREATE TABLE driver_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    document_type_id uuid NOT NULL REFERENCES driver_document_types(id) ON DELETE RESTRICT,
    series varchar(30) NULL,
    number varchar(100) NOT NULL,
    issued_at date NULL,
    valid_from date NULL,
    valid_until date NULL,
    issuer text NULL,
    status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    file_id uuid NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT fk_driver_documents_driver FOREIGN KEY (company_id, driver_id)
        REFERENCES drivers(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_driver_documents_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_driver_documents_dates CHECK (
        valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from
    ),
    CONSTRAINT ck_driver_documents_status CHECK (status IN ('ACTIVE','REVOKED','SUPERSEDED'))
);
CREATE INDEX ix_driver_documents_type
    ON driver_documents(company_id, driver_id, document_type_id);
CREATE INDEX ix_driver_documents_expiry ON driver_documents(company_id, valid_until);
CREATE INDEX ix_driver_documents_active_expiry
    ON driver_documents(driver_id, document_type_id, valid_until) WHERE status = 'ACTIVE';

ALTER TABLE users
    ADD CONSTRAINT fk_users_driver
    FOREIGN KEY (company_id, driver_id)
    REFERENCES drivers(company_id, id) ON DELETE RESTRICT;
