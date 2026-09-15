CREATE TABLE audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    actor_user_id uuid NULL,
    actor_role varchar(120) NULL,
    action varchar(120) NOT NULL,
    entity_type varchar(80) NOT NULL,
    entity_id uuid NULL,
    request_id uuid NOT NULL,
    correlation_id uuid NULL,
    source varchar(40) NOT NULL,
    ip_address inet NULL,
    user_agent text NULL,
    reason text NULL,
    before_data jsonb NULL,
    after_data jsonb NULL,
    changed_fields jsonb NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    entry_hash char(64) NULL,
    CONSTRAINT fk_audit_actor FOREIGN KEY (company_id, actor_user_id)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_audit_company_time ON audit_log(company_id, occurred_at DESC);
CREATE INDEX ix_audit_entity ON audit_log(company_id, entity_type, entity_id, occurred_at);
CREATE INDEX ix_audit_actor ON audit_log(company_id, actor_user_id, occurred_at);
CREATE INDEX ix_audit_request ON audit_log(request_id);
CREATE INDEX ix_audit_correlation ON audit_log(correlation_id) WHERE correlation_id IS NOT NULL;

CREATE TABLE audit_partition_seals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    period_from timestamptz NOT NULL,
    period_to timestamptz NOT NULL,
    row_count bigint NOT NULL,
    aggregate_hash char(64) NOT NULL,
    sealed_at timestamptz NOT NULL DEFAULT now(),
    storage_reference text NULL,
    CONSTRAINT uq_audit_seals_period UNIQUE (company_id, period_from, period_to),
    CONSTRAINT ck_audit_seals_period CHECK (period_to > period_from),
    CONSTRAINT ck_audit_seals_count CHECK (row_count >= 0)
);

CREATE TABLE outbox_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    aggregate_type varchar(80) NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type varchar(120) NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz NULL,
    attempt_count integer NOT NULL DEFAULT 0,
    last_attempt_at timestamptz NULL,
    last_error text NULL,
    CONSTRAINT ck_outbox_attempt_count CHECK (attempt_count >= 0)
);
CREATE INDEX ix_outbox_unpublished ON outbox_events(created_at) WHERE published_at IS NULL;
CREATE INDEX ix_outbox_aggregate
    ON outbox_events(company_id, aggregate_type, aggregate_id, created_at);

CREATE TABLE report_exports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    report_type varchar(100) NOT NULL,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_by uuid NOT NULL,
    requested_at timestamptz NOT NULL DEFAULT now(),
    status varchar(20) NOT NULL DEFAULT 'QUEUED',
    file_id uuid NULL,
    completed_at timestamptz NULL,
    error_code varchar(100) NULL,
    expires_at timestamptz NULL,
    CONSTRAINT fk_report_exports_user FOREIGN KEY (company_id, requested_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_report_exports_file FOREIGN KEY (company_id, file_id)
        REFERENCES files(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_report_exports_status CHECK (
        status IN ('QUEUED','RUNNING','READY','FAILED','EXPIRED')
    )
);
CREATE INDEX ix_report_exports_user
    ON report_exports(company_id, requested_by, requested_at DESC);
CREATE INDEX ix_report_exports_queue ON report_exports(status, requested_at);

CREATE TABLE system_integrity_alerts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    check_code varchar(120) NOT NULL,
    severity varchar(20) NOT NULL,
    entity_type varchar(80) NULL,
    entity_id uuid NULL,
    detected_at timestamptz NOT NULL DEFAULT now(),
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(20) NOT NULL DEFAULT 'OPEN',
    acknowledged_at timestamptz NULL,
    acknowledged_by uuid NULL,
    resolved_at timestamptz NULL,
    resolved_by uuid NULL,
    resolution_comment text NULL,
    CONSTRAINT fk_integrity_ack_actor FOREIGN KEY (company_id, acknowledged_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_integrity_resolve_actor FOREIGN KEY (company_id, resolved_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_integrity_severity CHECK (severity IN ('INFO','WARNING','ERROR','CRITICAL')),
    CONSTRAINT ck_integrity_status CHECK (status IN ('OPEN','ACKNOWLEDGED','RESOLVED'))
);
CREATE INDEX ix_integrity_open
    ON system_integrity_alerts(company_id, status, severity, detected_at DESC);
CREATE INDEX ix_integrity_check
    ON system_integrity_alerts(company_id, check_code, detected_at DESC);
CREATE INDEX ix_integrity_entity
    ON system_integrity_alerts(entity_type, entity_id) WHERE entity_id IS NOT NULL;

ALTER TABLE vehicle_odometer_readings
    ADD CONSTRAINT fk_odometer_trip
    FOREIGN KEY (company_id, trip_id)
    REFERENCES trips(company_id, id) ON DELETE RESTRICT;
ALTER TABLE vehicle_odometer_readings
    ADD CONSTRAINT fk_odometer_duty
    FOREIGN KEY (company_id, duty_id)
    REFERENCES duties(company_id, id) ON DELETE RESTRICT;
ALTER TABLE vehicle_odometer_readings
    ADD CONSTRAINT fk_odometer_waybill
    FOREIGN KEY (company_id, waybill_id)
    REFERENCES waybills(company_id, id) ON DELETE RESTRICT;
