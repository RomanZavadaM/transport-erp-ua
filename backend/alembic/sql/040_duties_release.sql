CREATE TABLE duties (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    depot_id uuid NULL,
    service_date date NOT NULL,
    duty_number varchar(80) NOT NULL,
    planned_start_at timestamptz NOT NULL,
    planned_end_at timestamptz NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'DRAFT',
    opened_at timestamptz NULL,
    opened_by uuid NULL,
    closed_at timestamptz NULL,
    closed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_duties_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_duties_number UNIQUE (company_id, duty_number),
    CONSTRAINT fk_duties_depot FOREIGN KEY (company_id, depot_id)
        REFERENCES depots(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duties_opened_by FOREIGN KEY (company_id, opened_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duties_closed_by FOREIGN KEY (company_id, closed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duties_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duties_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duties_plan_time CHECK (planned_end_at > planned_start_at),
    CONSTRAINT ck_duties_status CHECK (
        status IN ('DRAFT','PLANNED','ASSIGNED','RELEASE_PENDING','BLOCKED','READY','AUTHORIZED','ON_LINE','RETURNED','CLOSING','CLOSED','CANCELLED')
    )
);
CREATE INDEX ix_duties_company_date ON duties(company_id, service_date);
CREATE INDEX ix_duties_status_date ON duties(company_id, status, service_date);
CREATE INDEX ix_duties_depot_date ON duties(company_id, depot_id, service_date);

CREATE TABLE duty_trips (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    sequence_no integer NOT NULL,
    membership_status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    added_at timestamptz NOT NULL DEFAULT now(),
    added_by uuid NULL,
    removed_at timestamptz NULL,
    removed_by uuid NULL,
    reason text NULL,
    CONSTRAINT fk_duty_trips_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_trips_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_trips_added_by FOREIGN KEY (company_id, added_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_trips_removed_by FOREIGN KEY (company_id, removed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duty_trips_status CHECK (membership_status IN ('ACTIVE','REMOVED')),
    CONSTRAINT ck_duty_trips_sequence CHECK (sequence_no > 0)
);
CREATE UNIQUE INDEX ux_duty_trips_active_trip
    ON duty_trips(trip_id) WHERE membership_status = 'ACTIVE';
CREATE UNIQUE INDEX ux_duty_trips_active_sequence
    ON duty_trips(duty_id, sequence_no) WHERE membership_status = 'ACTIVE';

CREATE TABLE duty_vehicle_assignments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    assignment_period tstzrange NOT NULL,
    assignment_status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    assigned_at timestamptz NOT NULL DEFAULT now(),
    assigned_by uuid NULL,
    cancelled_at timestamptz NULL,
    cancelled_by uuid NULL,
    reason text NULL,
    CONSTRAINT fk_duty_vehicle_assignment_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_assignment_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_assignment_actor FOREIGN KEY (company_id, assigned_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_assignment_cancel_actor FOREIGN KEY (company_id, cancelled_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duty_vehicle_assignment_period CHECK (
        NOT isempty(assignment_period)
        AND lower(assignment_period) IS NOT NULL
        AND upper(assignment_period) IS NOT NULL
        AND lower_inc(assignment_period)
        AND NOT upper_inc(assignment_period)
    ),
    CONSTRAINT ck_duty_vehicle_assignment_status CHECK (
        assignment_status IN ('ACTIVE','CANCELLED','SUPERSEDED')
    ),
    EXCLUDE USING gist (
        company_id WITH =,
        vehicle_id WITH =,
        assignment_period WITH &&
    ) WHERE (assignment_status = 'ACTIVE'),
    EXCLUDE USING gist (
        duty_id WITH =,
        assignment_period WITH &&
    ) WHERE (assignment_status = 'ACTIVE')
);
CREATE INDEX ix_duty_vehicle_assignment_duty ON duty_vehicle_assignments(company_id, duty_id);
CREATE INDEX ix_duty_vehicle_assignment_vehicle ON duty_vehicle_assignments(company_id, vehicle_id);

CREATE TABLE duty_driver_assignments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    assignment_role varchar(30) NOT NULL,
    crew_mode varchar(20) NOT NULL DEFAULT 'SINGLE',
    assignment_period tstzrange NOT NULL,
    assignment_status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    assigned_at timestamptz NOT NULL DEFAULT now(),
    assigned_by uuid NULL,
    cancelled_at timestamptz NULL,
    cancelled_by uuid NULL,
    reason text NULL,
    CONSTRAINT fk_duty_driver_assignment_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_driver_assignment_driver FOREIGN KEY (company_id, driver_id)
        REFERENCES drivers(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_driver_assignment_actor FOREIGN KEY (company_id, assigned_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_driver_assignment_cancel_actor FOREIGN KEY (company_id, cancelled_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duty_driver_assignment_role CHECK (
        assignment_role IN ('PRIMARY','SECOND_DRIVER','RELIEF','TRAINEE')
    ),
    CONSTRAINT ck_duty_driver_assignment_crew CHECK (crew_mode IN ('SINGLE','CREW')),
    CONSTRAINT ck_duty_driver_assignment_period CHECK (
        NOT isempty(assignment_period)
        AND lower(assignment_period) IS NOT NULL
        AND upper(assignment_period) IS NOT NULL
        AND lower_inc(assignment_period)
        AND NOT upper_inc(assignment_period)
    ),
    CONSTRAINT ck_duty_driver_assignment_status CHECK (
        assignment_status IN ('ACTIVE','CANCELLED','SUPERSEDED')
    ),
    EXCLUDE USING gist (
        company_id WITH =,
        driver_id WITH =,
        assignment_period WITH &&
    ) WHERE (assignment_status = 'ACTIVE')
);
CREATE INDEX ix_duty_driver_assignment_duty ON duty_driver_assignments(company_id, duty_id);
CREATE INDEX ix_duty_driver_assignment_driver ON duty_driver_assignments(company_id, driver_id);

CREATE TABLE duty_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    event_type varchar(80) NOT NULL,
    occurred_at timestamptz NOT NULL,
    source varchar(30) NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_duty_events_company_id UNIQUE (company_id, id),
    CONSTRAINT fk_duty_events_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_events_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_duty_events_timeline ON duty_events(company_id, duty_id, occurred_at);

CREATE TABLE duty_vehicle_usage (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    actual_period tstzrange NOT NULL,
    source varchar(30) NOT NULL,
    started_event_id uuid NULL,
    ended_event_id uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_duty_vehicle_usage_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_usage_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_usage_start_event FOREIGN KEY (company_id, started_event_id)
        REFERENCES duty_events(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_vehicle_usage_end_event FOREIGN KEY (company_id, ended_event_id)
        REFERENCES duty_events(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duty_vehicle_usage_period CHECK (
        NOT isempty(actual_period) AND lower(actual_period) IS NOT NULL
    )
);
CREATE INDEX ix_duty_vehicle_usage_duty ON duty_vehicle_usage(company_id, duty_id);
CREATE INDEX ix_duty_vehicle_usage_vehicle ON duty_vehicle_usage(company_id, vehicle_id);

CREATE TABLE duty_driver_usage (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    usage_role varchar(30) NOT NULL,
    crew_mode varchar(20) NOT NULL DEFAULT 'SINGLE',
    actual_period tstzrange NOT NULL,
    source varchar(30) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_duty_driver_usage_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_duty_driver_usage_driver FOREIGN KEY (company_id, driver_id)
        REFERENCES drivers(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_duty_driver_usage_role CHECK (
        usage_role IN ('PRIMARY','SECOND_DRIVER','RELIEF','TRAINEE')
    ),
    CONSTRAINT ck_duty_driver_usage_crew CHECK (crew_mode IN ('SINGLE','CREW')),
    CONSTRAINT ck_duty_driver_usage_period CHECK (
        NOT isempty(actual_period) AND lower(actual_period) IS NOT NULL
    )
);
CREATE INDEX ix_duty_driver_usage_duty ON duty_driver_usage(company_id, duty_id);
CREATE INDEX ix_duty_driver_usage_driver ON duty_driver_usage(company_id, driver_id);

ALTER TABLE vehicle_runtime_state
    ADD CONSTRAINT fk_vehicle_runtime_duty
    FOREIGN KEY (company_id, current_duty_id)
    REFERENCES duties(company_id, id) ON DELETE RESTRICT;

CREATE TABLE releases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    duty_id uuid NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'OPEN',
    opened_at timestamptz NOT NULL DEFAULT now(),
    opened_by uuid NULL,
    evaluation_started_at timestamptz NULL,
    ready_at timestamptz NULL,
    authorized_at timestamptz NULL,
    authorized_by uuid NULL,
    actual_departure_at timestamptz NULL,
    blocked_code varchar(100) NULL,
    blocked_comment text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_releases_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_releases_duty UNIQUE (duty_id),
    CONSTRAINT fk_releases_duty FOREIGN KEY (company_id, duty_id)
        REFERENCES duties(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_releases_opened_by FOREIGN KEY (company_id, opened_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_releases_authorized_by FOREIGN KEY (company_id, authorized_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_releases_status CHECK (
        status IN ('OPEN','WAITING_CHECKS','EVALUATING','BLOCKED','READY','AUTHORIZED','USED')
    )
);

CREATE TABLE check_templates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    check_type varchar(40) NOT NULL,
    name text NOT NULL,
    version_no integer NOT NULL,
    valid_period daterange NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_check_templates_type CHECK (
        check_type IN ('MEDICAL','TECHNICAL','DRIVER_TECHNICAL_PREDEPARTURE')
    ),
    CONSTRAINT ck_check_templates_period CHECK (NOT isempty(valid_period)),
    CONSTRAINT ck_check_templates_version CHECK (version_no > 0)
);
CREATE UNIQUE INDEX ux_check_templates_tenant_version
    ON check_templates(company_id, check_type, name, version_no) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_check_templates_system_version
    ON check_templates(check_type, name, version_no) WHERE company_id IS NULL;

CREATE TABLE check_template_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id uuid NOT NULL REFERENCES check_templates(id) ON DELETE RESTRICT,
    code varchar(80) NOT NULL,
    sequence_no integer NOT NULL,
    label_key varchar(160) NOT NULL,
    value_type varchar(30) NOT NULL,
    required boolean NOT NULL,
    blocking_on_failure boolean NOT NULL DEFAULT false,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_check_template_item_code UNIQUE (template_id, code),
    CONSTRAINT uq_check_template_item_sequence UNIQUE (template_id, sequence_no),
    CONSTRAINT ck_check_template_item_sequence CHECK (sequence_no > 0)
);

CREATE TABLE pre_trip_checks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    release_id uuid NOT NULL,
    template_id uuid NULL REFERENCES check_templates(id) ON DELETE RESTRICT,
    check_type varchar(40) NOT NULL,
    subject_type varchar(30) NOT NULL,
    subject_id uuid NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'PENDING',
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    performed_by uuid NOT NULL,
    valid_until timestamptz NULL,
    comment text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_pre_trip_checks_company_id UNIQUE (company_id, id),
    CONSTRAINT fk_pre_trip_checks_release FOREIGN KEY (company_id, release_id)
        REFERENCES releases(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_pre_trip_checks_actor FOREIGN KEY (company_id, performed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_pre_trip_checks_type CHECK (
        check_type IN ('MEDICAL','TECHNICAL','DRIVER_TECHNICAL_PREDEPARTURE')
    ),
    CONSTRAINT ck_pre_trip_checks_status CHECK (
        status IN ('PENDING','IN_PROGRESS','PASSED','FAILED')
    ),
    CONSTRAINT ck_pre_trip_checks_completion CHECK (
        (status IN ('PASSED','FAILED') AND completed_at IS NOT NULL)
        OR status IN ('PENDING','IN_PROGRESS')
    )
);
CREATE INDEX ix_pre_trip_checks_release_type
    ON pre_trip_checks(release_id, check_type, completed_at DESC);

CREATE TABLE medical_check_details (
    pre_trip_check_id uuid PRIMARY KEY,
    company_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    fitness_result varchar(20) NOT NULL,
    CONSTRAINT fk_medical_check FOREIGN KEY (company_id, pre_trip_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_medical_driver FOREIGN KEY (company_id, driver_id)
        REFERENCES drivers(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_medical_fitness CHECK (fitness_result IN ('FIT','UNFIT'))
);

CREATE TABLE technical_check_details (
    pre_trip_check_id uuid PRIMARY KEY,
    company_id uuid NOT NULL,
    vehicle_id uuid NOT NULL,
    odometer_km bigint NOT NULL,
    result varchar(20) NOT NULL,
    blocking_defect_found boolean NOT NULL DEFAULT false,
    inspection_place text NULL,
    CONSTRAINT fk_technical_check FOREIGN KEY (company_id, pre_trip_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_technical_vehicle FOREIGN KEY (company_id, vehicle_id)
        REFERENCES vehicles(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_technical_odometer CHECK (odometer_km >= 0),
    CONSTRAINT ck_technical_result CHECK (result IN ('PASSED','FAILED'))
);

CREATE TABLE check_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    pre_trip_check_id uuid NOT NULL,
    template_item_id uuid NOT NULL REFERENCES check_template_items(id) ON DELETE RESTRICT,
    result_value jsonb NOT NULL,
    passed boolean NULL,
    comment text NULL,
    CONSTRAINT uq_check_results_item UNIQUE (pre_trip_check_id, template_item_id),
    CONSTRAINT fk_check_results_check FOREIGN KEY (company_id, pre_trip_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT
);

CREATE TABLE pre_trip_check_invalidations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    pre_trip_check_id uuid NOT NULL UNIQUE,
    reason text NOT NULL,
    invalidated_at timestamptz NOT NULL DEFAULT now(),
    invalidated_by uuid NOT NULL,
    replacement_check_id uuid NULL,
    CONSTRAINT fk_check_invalidation_original FOREIGN KEY (company_id, pre_trip_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_check_invalidation_replacement FOREIGN KEY (company_id, replacement_check_id)
        REFERENCES pre_trip_checks(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_check_invalidation_actor FOREIGN KEY (company_id, invalidated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);

CREATE TABLE compliance_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(120) NOT NULL,
    scope varchar(50) NOT NULL,
    severity varchar(20) NOT NULL,
    blocking boolean NOT NULL,
    valid_period daterange NOT NULL,
    applicability jsonb NOT NULL DEFAULT '{}'::jsonb,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT ck_compliance_rules_period CHECK (NOT isempty(valid_period)),
    CONSTRAINT ck_compliance_rules_severity CHECK (
        severity IN ('INFO','WARNING','ERROR','CRITICAL')
    )
);
CREATE UNIQUE INDEX ux_compliance_rules_tenant_code_period
    ON compliance_rules(company_id, code, valid_period) WHERE company_id IS NOT NULL;
CREATE UNIQUE INDEX ux_compliance_rules_system_code_period
    ON compliance_rules(code, valid_period) WHERE company_id IS NULL;

CREATE TABLE release_rule_evaluations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    release_id uuid NOT NULL,
    evaluation_batch_id uuid NOT NULL,
    rule_id uuid NULL REFERENCES compliance_rules(id) ON DELETE RESTRICT,
    rule_code varchar(120) NOT NULL,
    evaluated_at timestamptz NOT NULL DEFAULT now(),
    result varchar(30) NOT NULL,
    blocking boolean NOT NULL,
    subject_type varchar(30) NULL,
    subject_id uuid NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT fk_release_evaluation_release FOREIGN KEY (company_id, release_id)
        REFERENCES releases(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_release_evaluation_result CHECK (
        result IN ('PASS','FAIL','WARNING','NOT_APPLICABLE')
    ),
    CONSTRAINT uq_release_evaluation_result UNIQUE NULLS NOT DISTINCT (
        release_id, evaluation_batch_id, rule_code, subject_type, subject_id
    )
);
CREATE INDEX ix_release_evaluation_batch
    ON release_rule_evaluations(release_id, evaluation_batch_id);

CREATE TABLE release_authorizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    release_id uuid NOT NULL,
    decision varchar(20) NOT NULL,
    authorized_at timestamptz NOT NULL DEFAULT now(),
    authorized_by uuid NOT NULL,
    comment text NULL,
    evaluation_batch_id uuid NULL,
    rule_evaluation_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_release_authorization_release FOREIGN KEY (company_id, release_id)
        REFERENCES releases(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_release_authorization_actor FOREIGN KEY (company_id, authorized_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_release_authorization_decision CHECK (decision IN ('AUTHORIZED','REJECTED'))
);
CREATE UNIQUE INDEX ux_release_authorized_once
    ON release_authorizations(release_id) WHERE decision = 'AUTHORIZED';
