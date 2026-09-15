CREATE TABLE number_sequences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    document_type varchar(60) NOT NULL,
    series varchar(30) NOT NULL,
    year integer NOT NULL,
    prefix varchar(30) NULL,
    suffix varchar(30) NULL,
    next_value bigint NOT NULL DEFAULT 1,
    active boolean NOT NULL DEFAULT true,
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_number_sequences_scope UNIQUE (company_id, document_type, series, year),
    CONSTRAINT ck_number_sequences_value CHECK (next_value > 0)
);

CREATE TABLE document_templates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    document_type varchar(60) NOT NULL,
    code varchar(80) NOT NULL,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_document_templates_tenant_code
    ON document_templates(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_document_templates_system_code
    ON document_templates(code) WHERE company_id IS NULL;

CREATE TABLE document_template_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id uuid NOT NULL REFERENCES document_templates(id) ON DELETE RESTRICT,
    version_no integer NOT NULL,
    locale varchar(5) NOT NULL,
    valid_period daterange NOT NULL,
    html_template text NOT NULL,
    css_template text NOT NULL,
    input_schema jsonb NOT NULL,
    engine varchar(40) NOT NULL DEFAULT 'HTML_PDF',
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_document_template_versions UNIQUE (template_id, version_no, locale),
    CONSTRAINT ck_document_template_version_locale CHECK (locale IN ('uk','en','es','fr','de')),
    CONSTRAINT ck_document_template_version_period CHECK (NOT isempty(valid_period)),
    CONSTRAINT ck_document_template_version_number CHECK (version_no > 0)
);

CREATE TABLE files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    storage_provider varchar(30) NOT NULL,
    storage_key text NOT NULL,
    original_filename text NOT NULL,
    mime_type varchar(120) NOT NULL,
    size_bytes bigint NOT NULL,
    sha256 char(64) NOT NULL,
    retention_class varchar(60) NULL,
    retain_until date NULL,
    legal_hold boolean NOT NULL DEFAULT false,
    retention_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT uq_files_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_files_storage_key UNIQUE (storage_provider, storage_key),
    CONSTRAINT fk_files_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_files_size CHECK (size_bytes >= 0)
);

ALTER TABLE vehicle_documents
    ADD CONSTRAINT fk_vehicle_documents_file
    FOREIGN KEY (company_id, file_id)
    REFERENCES files(company_id, id) ON DELETE RESTRICT;
ALTER TABLE driver_documents
    ADD CONSTRAINT fk_driver_documents_file
    FOREIGN KEY (company_id, file_id)
    REFERENCES files(company_id, id) ON DELETE RESTRICT;

CREATE TABLE waybills (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    document_role varchar(40) NOT NULL DEFAULT 'PRIMARY',
    series varchar(30) NOT NULL,
    number bigint NOT NULL,
    full_number varchar(100) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'DRAFT',
    current_version_id uuid NULL,
    issued_at timestamptz NULL,
    issued_by uuid NULL,
    returned_at timestamptz NULL,
    closed_at timestamptz NULL,
    closed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_waybills_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_waybills_full_number UNIQUE (company_id, full_number),
    CONSTRAINT fk_waybills_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybills_issued_by FOREIGN KEY (company_id, issued_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybills_closed_by FOREIGN KEY (company_id, closed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybills_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_waybills_document_role CHECK (char_length(document_role) > 0),
    CONSTRAINT ck_waybills_status CHECK (
        status IN ('DRAFT','GENERATED','ISSUED','ACTIVE','RETURNED','CLOSING','CLOSED','CANCELLED')
    )
);
CREATE UNIQUE INDEX ux_waybills_primary_per_duty
    ON waybills(duty_id)
    WHERE document_role = 'PRIMARY' AND status <> 'CANCELLED';
CREATE INDEX ix_waybills_company_status ON waybills(company_id, status, created_at);

CREATE TABLE waybill_trips (
    waybill_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    company_id uuid NOT NULL,
    sequence_no integer NOT NULL,
    PRIMARY KEY (waybill_id, trip_id),
    CONSTRAINT uq_waybill_trips_sequence UNIQUE (waybill_id, sequence_no),
    CONSTRAINT fk_waybill_trips_waybill FOREIGN KEY (company_id, waybill_id)
        REFERENCES waybills(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybill_trips_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_waybill_trips_sequence CHECK (sequence_no > 0)
);

CREATE TABLE waybill_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    waybill_id uuid NOT NULL,
    version_no integer NOT NULL,
    document_template_version_id uuid NOT NULL REFERENCES document_template_versions(id) ON DELETE RESTRICT,
    snapshot jsonb NOT NULL,
    snapshot_schema_version integer NOT NULL,
    snapshot_sha256 char(64) NOT NULL,
    pdf_file_id uuid NULL,
    pdf_sha256 char(64) NULL,
    generation_status varchar(20) NOT NULL DEFAULT 'PENDING',
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    previous_version_id uuid NULL REFERENCES waybill_versions(id) ON DELETE RESTRICT,
    correction_case_id uuid NULL REFERENCES correction_cases(id) ON DELETE RESTRICT,
    correction_reason text NULL,
    CONSTRAINT uq_waybill_versions_number UNIQUE (waybill_id, version_no),
    CONSTRAINT uq_waybill_versions_waybill_id UNIQUE (waybill_id, id),
    CONSTRAINT fk_waybill_versions_waybill FOREIGN KEY (company_id, waybill_id)
        REFERENCES waybills(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybill_versions_file FOREIGN KEY (company_id, pdf_file_id)
        REFERENCES files(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_waybill_versions_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_waybill_versions_status CHECK (generation_status IN ('PENDING','READY','FAILED')),
    CONSTRAINT ck_waybill_versions_schema_version CHECK (snapshot_schema_version > 0)
);
CREATE INDEX ix_waybill_versions_order ON waybill_versions(waybill_id, version_no DESC);

ALTER TABLE waybills
    ADD CONSTRAINT fk_waybills_current_version
    FOREIGN KEY (id, current_version_id)
    REFERENCES waybill_versions(waybill_id, id) ON DELETE RESTRICT;

CREATE TABLE entity_attachments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    entity_type varchar(60) NOT NULL,
    entity_id uuid NOT NULL,
    file_id uuid NOT NULL,
    attachment_type varchar(60) NOT NULL,
    description text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT fk_entity_attachments_file FOREIGN KEY (company_id, file_id)
        REFERENCES files(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_entity_attachments_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_entity_attachments_entity ON entity_attachments(company_id, entity_type, entity_id);

CREATE TABLE fuel_operations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    vehicle_id uuid NOT NULL,
    duty_id uuid NULL,
    trip_id uuid NULL,
    waybill_id uuid NULL,
    operation_type varchar(30) NOT NULL,
    fuel_type_id uuid NOT NULL REFERENCES fuel_types(id) ON DELETE RESTRICT,
    quantity_l numeric(12,3) NOT NULL,
    unit_price numeric(14,4) NULL,
    amount numeric(14,2) NULL,
    odometer_km bigint NULL,
    operation_at timestamptz NOT NULL,
    document_number varchar(100) NULL,
    source varchar(30) NOT NULL,
    reversal_of_id uuid NULL REFERENCES fuel_operations(id) ON DELETE RESTRICT,
    created_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_fuel_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_fuel_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_fuel_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_fuel_waybill FOREIGN KEY (company_id, waybill_id)
        REFERENCES waybills(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_fuel_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_fuel_quantity CHECK (quantity_l > 0),
    CONSTRAINT ck_fuel_odometer CHECK (odometer_km IS NULL OR odometer_km >= 0),
    CONSTRAINT ck_fuel_operation_type CHECK (
        operation_type IN ('REFUEL','ISSUE','RETURN','CONSUMPTION','ADJUSTMENT','REVERSAL')
    )
);
CREATE INDEX ix_fuel_vehicle_time ON fuel_operations(company_id, vehicle_id, operation_at);
CREATE INDEX ix_fuel_company_time ON fuel_operations(company_id, operation_at);
CREATE INDEX ix_fuel_duty ON fuel_operations(duty_id);
CREATE INDEX ix_fuel_waybill ON fuel_operations(waybill_id);

CREATE TABLE defects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    vehicle_id uuid NOT NULL,
    reported_at timestamptz NOT NULL,
    reported_by uuid NULL,
    source varchar(30) NOT NULL,
    trip_id uuid NULL,
    duty_id uuid NULL,
    technical_check_id uuid NULL,
    severity varchar(20) NOT NULL,
    description text NOT NULL,
    blocks_release boolean NOT NULL DEFAULT false,
    status varchar(30) NOT NULL DEFAULT 'OPEN',
    resolved_at timestamptz NULL,
    resolved_by uuid NULL,
    resolution_comment text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_defects_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_defects_reported_by FOREIGN KEY (company_id, reported_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_defects_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_defects_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_defects_technical_check FOREIGN KEY (company_id, technical_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_defects_resolved_by FOREIGN KEY (company_id, resolved_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_defects_status CHECK (
        status IN ('OPEN','ACKNOWLEDGED','IN_REPAIR','RESOLVED','CLOSED')
    )
);
CREATE INDEX ix_defects_vehicle_status ON defects(company_id, vehicle_id, status);
CREATE INDEX ix_defects_blocking_open ON defects(vehicle_id)
    WHERE blocks_release = true AND status NOT IN ('RESOLVED','CLOSED');

CREATE TABLE maintenance_types (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(60) NOT NULL,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true
);
CREATE UNIQUE INDEX ux_maintenance_types_tenant_code
    ON maintenance_types(company_id, code) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_maintenance_types_system_code
    ON maintenance_types(code) WHERE company_id IS NULL;

CREATE TABLE maintenance_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    vehicle_id uuid NOT NULL,
    maintenance_type_id uuid NOT NULL REFERENCES maintenance_types(id) ON DELETE RESTRICT,
    interval_km bigint NULL,
    interval_days integer NULL,
    last_completed_date date NULL,
    last_completed_odometer bigint NULL,
    next_due_date date NULL,
    next_due_odometer bigint NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_maintenance_plan_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_maintenance_interval_km CHECK (interval_km IS NULL OR interval_km > 0),
    CONSTRAINT ck_maintenance_interval_days CHECK (interval_days IS NULL OR interval_days > 0),
    CONSTRAINT ck_maintenance_interval_present CHECK (interval_km IS NOT NULL OR interval_days IS NOT NULL),
    CONSTRAINT ck_maintenance_last_odometer CHECK (
        last_completed_odometer IS NULL OR last_completed_odometer >= 0
    ),
    CONSTRAINT ck_maintenance_next_odometer CHECK (next_due_odometer IS NULL OR next_due_odometer >= 0)
);

CREATE TABLE maintenance_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    vehicle_id uuid NOT NULL,
    maintenance_plan_id uuid NULL REFERENCES maintenance_plans(id) ON DELETE RESTRICT,
    status varchar(20) NOT NULL DEFAULT 'OPEN',
    opened_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    odometer_km bigint NULL,
    provider text NULL,
    cost numeric(14,2) NULL,
    comment text NULL,
    created_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_maintenance_event_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_maintenance_event_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_maintenance_event_status CHECK (
        status IN ('OPEN','IN_PROGRESS','COMPLETED','CANCELLED')
    ),
    CONSTRAINT ck_maintenance_event_odometer CHECK (odometer_km IS NULL OR odometer_km >= 0),
    CONSTRAINT ck_maintenance_event_cost CHECK (cost IS NULL OR cost >= 0)
);

CREATE TABLE repair_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    vehicle_id uuid NOT NULL,
    number varchar(80) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'OPEN',
    blocks_operation boolean NOT NULL DEFAULT false,
    opened_at timestamptz NOT NULL DEFAULT now(),
    opened_by uuid NOT NULL,
    planned_start timestamptz NULL,
    actual_start timestamptz NULL,
    actual_finish timestamptz NULL,
    odometer_km bigint NULL,
    description text NOT NULL,
    total_cost numeric(14,2) NULL,
    closed_at timestamptz NULL,
    closed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_repair_orders_number UNIQUE (company_id, number),
    CONSTRAINT fk_repair_orders_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_repair_orders_opened_by FOREIGN KEY (company_id, opened_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_repair_orders_closed_by FOREIGN KEY (company_id, closed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_repair_orders_status CHECK (
        status IN ('OPEN','DIAGNOSIS','APPROVED','IN_PROGRESS','WAITING_PARTS','COMPLETED','VERIFIED','CLOSED','CANCELLED')
    ),
    CONSTRAINT ck_repair_orders_odometer CHECK (odometer_km IS NULL OR odometer_km >= 0),
    CONSTRAINT ck_repair_orders_cost CHECK (total_cost IS NULL OR total_cost >= 0),
    CONSTRAINT ck_repair_orders_time CHECK (
        actual_finish IS NULL OR actual_start IS NULL OR actual_finish >= actual_start
    )
);
CREATE INDEX ix_repair_orders_vehicle_status ON repair_orders(vehicle_id, status);
CREATE INDEX ix_repair_orders_blocking ON repair_orders(vehicle_id)
    WHERE blocks_operation = true AND status NOT IN ('CLOSED','CANCELLED');

CREATE TABLE repair_order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    repair_order_id uuid NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    item_type varchar(30) NOT NULL,
    description text NOT NULL,
    part_number varchar(100) NULL,
    quantity numeric(12,3) NOT NULL,
    unit varchar(20) NOT NULL,
    unit_price numeric(14,4) NULL,
    amount numeric(14,2) NULL,
    CONSTRAINT ck_repair_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT ck_repair_order_item_price CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT ck_repair_order_item_amount CHECK (amount IS NULL OR amount >= 0)
);
