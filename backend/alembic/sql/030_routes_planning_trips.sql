CREATE TABLE correction_cases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    entity_type varchar(60) NOT NULL,
    entity_id uuid NOT NULL,
    reason_code varchar(80) NOT NULL,
    reason text NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'OPEN',
    requested_at timestamptz NOT NULL DEFAULT now(),
    requested_by uuid NOT NULL,
    approved_at timestamptz NULL,
    approved_by uuid NULL,
    completed_at timestamptz NULL,
    completed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_corrections_requested_by FOREIGN KEY (company_id, requested_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_corrections_approved_by FOREIGN KEY (company_id, approved_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_corrections_completed_by FOREIGN KEY (company_id, completed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_correction_status CHECK (
        status IN ('OPEN','APPROVED','REJECTED','COMPLETED','CANCELLED')
    )
);
CREATE INDEX ix_correction_entity ON correction_cases(company_id, entity_type, entity_id);
CREATE INDEX ix_correction_status ON correction_cases(company_id, status, requested_at);

CREATE TABLE stops (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    code varchar(40) NOT NULL,
    name text NOT NULL,
    latitude numeric(9,6) NULL,
    longitude numeric(9,6) NULL,
    address text NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_stops_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_stops_company_code UNIQUE (company_id, code),
    CONSTRAINT ck_stops_latitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CONSTRAINT ck_stops_longitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);

CREATE TABLE routes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    route_number varchar(30) NOT NULL,
    name text NOT NULL,
    route_type varchar(40) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_routes_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_routes_number UNIQUE (company_id, route_number),
    CONSTRAINT fk_routes_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_routes_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT
);

CREATE TABLE route_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    route_id uuid NOT NULL,
    version_no integer NOT NULL,
    valid_period daterange NOT NULL,
    public_name text NULL,
    planned_distance_km numeric(12,3) NULL,
    status varchar(20) NOT NULL DEFAULT 'DRAFT',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT uq_route_versions_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_route_versions_number UNIQUE (route_id, version_no),
    CONSTRAINT fk_route_versions_route FOREIGN KEY (company_id, route_id)
        REFERENCES routes(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_route_versions_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_route_versions_period CHECK (NOT isempty(valid_period)),
    CONSTRAINT ck_route_versions_status CHECK (status IN ('DRAFT','ACTIVE','RETIRED')),
    CONSTRAINT ck_route_versions_distance CHECK (
        planned_distance_km IS NULL OR planned_distance_km >= 0
    ),
    EXCLUDE USING gist (route_id WITH =, valid_period WITH &&)
        WHERE (status = 'ACTIVE')
);

CREATE TABLE route_stops (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    route_version_id uuid NOT NULL,
    direction smallint NOT NULL,
    sequence_no integer NOT NULL,
    stop_id uuid NOT NULL,
    distance_from_start_km numeric(12,3) NOT NULL,
    planned_travel_seconds integer NULL,
    planned_dwell_seconds integer NULL,
    CONSTRAINT uq_route_stops_order UNIQUE (route_version_id, direction, sequence_no),
    CONSTRAINT fk_route_stops_version FOREIGN KEY (company_id, route_version_id)
        REFERENCES route_versions(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_route_stops_stop FOREIGN KEY (company_id, stop_id)
        REFERENCES stops(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_route_stops_sequence CHECK (sequence_no > 0),
    CONSTRAINT ck_route_stops_direction CHECK (direction >= 0),
    CONSTRAINT ck_route_stops_distance CHECK (distance_from_start_km >= 0),
    CONSTRAINT ck_route_stops_travel CHECK (
        planned_travel_seconds IS NULL OR planned_travel_seconds >= 0
    ),
    CONSTRAINT ck_route_stops_dwell CHECK (
        planned_dwell_seconds IS NULL OR planned_dwell_seconds >= 0
    )
);

CREATE TABLE schedules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    route_id uuid NOT NULL,
    code varchar(50) NOT NULL,
    name text NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'DRAFT',
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_schedules_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_schedules_code UNIQUE (company_id, code),
    CONSTRAINT fk_schedules_route FOREIGN KEY (company_id, route_id)
        REFERENCES routes(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedules_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedules_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_schedules_status CHECK (status IN ('DRAFT','ACTIVE','RETIRED'))
);

CREATE TABLE schedule_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    schedule_id uuid NOT NULL,
    version_no integer NOT NULL,
    route_version_id uuid NOT NULL,
    valid_period daterange NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'DRAFT',
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT uq_schedule_versions_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_schedule_versions_number UNIQUE (schedule_id, version_no),
    CONSTRAINT fk_schedule_versions_schedule FOREIGN KEY (company_id, schedule_id)
        REFERENCES schedules(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedule_versions_route FOREIGN KEY (company_id, route_version_id)
        REFERENCES route_versions(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedule_versions_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_schedule_versions_period CHECK (NOT isempty(valid_period)),
    CONSTRAINT ck_schedule_versions_status CHECK (status IN ('DRAFT','ACTIVE','RETIRED')),
    EXCLUDE USING gist (schedule_id WITH =, valid_period WITH &&)
        WHERE (status = 'ACTIVE')
);

CREATE TABLE service_calendars (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    name text NOT NULL,
    monday boolean NOT NULL,
    tuesday boolean NOT NULL,
    wednesday boolean NOT NULL,
    thursday boolean NOT NULL,
    friday boolean NOT NULL,
    saturday boolean NOT NULL,
    sunday boolean NOT NULL,
    valid_period daterange NOT NULL,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT uq_service_calendars_company_id UNIQUE (company_id, id),
    CONSTRAINT ck_service_calendars_period CHECK (NOT isempty(valid_period))
);

CREATE TABLE service_calendar_exceptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    service_calendar_id uuid NOT NULL,
    service_date date NOT NULL,
    operation varchar(10) NOT NULL,
    comment text NULL,
    CONSTRAINT uq_calendar_exception UNIQUE (service_calendar_id, service_date),
    CONSTRAINT fk_calendar_exception_calendar FOREIGN KEY (company_id, service_calendar_id)
        REFERENCES service_calendars(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_calendar_exception_operation CHECK (operation IN ('ADD','REMOVE'))
);

CREATE TABLE schedule_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    schedule_version_id uuid NOT NULL,
    service_calendar_id uuid NOT NULL,
    run_code varchar(50) NOT NULL,
    direction smallint NOT NULL,
    departure_time time NOT NULL,
    arrival_time time NOT NULL,
    arrival_day_offset smallint NOT NULL DEFAULT 0,
    active boolean NOT NULL DEFAULT true,
    CONSTRAINT uq_schedule_runs_company_id UNIQUE (company_id, id),
    CONSTRAINT uq_schedule_runs_code UNIQUE (schedule_version_id, run_code),
    CONSTRAINT fk_schedule_runs_version FOREIGN KEY (company_id, schedule_version_id)
        REFERENCES schedule_versions(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_schedule_runs_calendar FOREIGN KEY (company_id, service_calendar_id)
        REFERENCES service_calendars(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_schedule_runs_offset CHECK (arrival_day_offset >= 0),
    CONSTRAINT ck_schedule_runs_direction CHECK (direction >= 0)
);

CREATE TABLE schedule_stop_times (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    schedule_run_id uuid NOT NULL,
    route_stop_id uuid NOT NULL REFERENCES route_stops(id) ON DELETE RESTRICT,
    sequence_no integer NOT NULL,
    arrival_offset_seconds integer NULL,
    departure_offset_seconds integer NULL,
    CONSTRAINT uq_schedule_stop_times_order UNIQUE (schedule_run_id, sequence_no),
    CONSTRAINT fk_schedule_stop_times_run FOREIGN KEY (company_id, schedule_run_id)
        REFERENCES schedule_runs(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_schedule_stop_times_sequence CHECK (sequence_no > 0),
    CONSTRAINT ck_schedule_stop_times_arrival CHECK (
        arrival_offset_seconds IS NULL OR arrival_offset_seconds >= 0
    ),
    CONSTRAINT ck_schedule_stop_times_departure CHECK (
        departure_offset_seconds IS NULL OR departure_offset_seconds >= 0
    )
);

CREATE TABLE trips (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    service_date date NOT NULL,
    schedule_run_id uuid NULL,
    route_version_id uuid NOT NULL,
    trip_number varchar(80) NULL,
    planned_departure_at timestamptz NOT NULL,
    planned_arrival_at timestamptz NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'DRAFT',
    cancel_reason_code varchar(80) NULL,
    cancel_comment text NULL,
    effective_actual_snapshot_id uuid NULL,
    closed_at timestamptz NULL,
    closed_by uuid NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT uq_trips_company_id UNIQUE (company_id, id),
    CONSTRAINT fk_trips_schedule_run FOREIGN KEY (company_id, schedule_run_id)
        REFERENCES schedule_runs(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trips_route_version FOREIGN KEY (company_id, route_version_id)
        REFERENCES route_versions(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trips_closed_by FOREIGN KEY (company_id, closed_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trips_created_by FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trips_updated_by FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trips_plan_time CHECK (planned_arrival_at > planned_departure_at),
    CONSTRAINT ck_trips_status CHECK (
        status IN ('DRAFT','PLANNED','SCHEDULED','READY','RELEASED','IN_PROGRESS','COMPLETED','CLOSED','CANCELLED')
    )
);
CREATE UNIQUE INDEX ux_trips_generated
    ON trips(schedule_run_id, service_date) WHERE schedule_run_id IS NOT NULL;
CREATE INDEX ix_trips_company_date ON trips(company_id, service_date);
CREATE INDEX ix_trips_company_status_date ON trips(company_id, status, service_date);
CREATE INDEX ix_trips_route_date ON trips(route_version_id, service_date);
CREATE INDEX ix_trips_planned_departure ON trips(planned_departure_at);

CREATE TABLE trip_stop_plan (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    stop_id uuid NOT NULL,
    route_stop_id uuid NULL REFERENCES route_stops(id) ON DELETE RESTRICT,
    sequence_no integer NOT NULL,
    planned_arrival_at timestamptz NULL,
    planned_departure_at timestamptz NULL,
    CONSTRAINT uq_trip_stop_plan_order UNIQUE (trip_id, sequence_no),
    CONSTRAINT fk_trip_stop_plan_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_stop_plan_stop FOREIGN KEY (company_id, stop_id)
        REFERENCES stops(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trip_stop_plan_sequence CHECK (sequence_no > 0)
);

CREATE TABLE trip_actuals (
    trip_id uuid PRIMARY KEY,
    company_id uuid NOT NULL,
    actual_departure_at timestamptz NULL,
    actual_arrival_at timestamptz NULL,
    departure_odometer_km bigint NULL,
    arrival_odometer_km bigint NULL,
    actual_distance_km numeric(12,3) NULL,
    fuel_departure_l numeric(12,3) NULL,
    fuel_arrival_l numeric(12,3) NULL,
    origin_source varchar(30) NOT NULL DEFAULT 'MANUAL',
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid NULL,
    row_version bigint NOT NULL DEFAULT 1,
    CONSTRAINT fk_trip_actuals_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_actuals_actor FOREIGN KEY (company_id, updated_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trip_actuals_odometer CHECK (
        arrival_odometer_km IS NULL OR departure_odometer_km IS NULL
        OR arrival_odometer_km >= departure_odometer_km
    ),
    CONSTRAINT ck_trip_actuals_time CHECK (
        actual_arrival_at IS NULL OR actual_departure_at IS NULL
        OR actual_arrival_at >= actual_departure_at
    ),
    CONSTRAINT ck_trip_actuals_distance CHECK (actual_distance_km IS NULL OR actual_distance_km >= 0),
    CONSTRAINT ck_trip_actuals_fuel_out CHECK (fuel_departure_l IS NULL OR fuel_departure_l >= 0),
    CONSTRAINT ck_trip_actuals_fuel_in CHECK (fuel_arrival_l IS NULL OR fuel_arrival_l >= 0)
);

CREATE TABLE trip_stop_actuals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    stop_id uuid NOT NULL,
    sequence_no integer NOT NULL,
    actual_arrival_at timestamptz NULL,
    actual_departure_at timestamptz NULL,
    source varchar(30) NOT NULL,
    CONSTRAINT uq_trip_stop_actual_order UNIQUE (trip_id, sequence_no),
    CONSTRAINT fk_trip_stop_actual_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_stop_actual_stop FOREIGN KEY (company_id, stop_id)
        REFERENCES stops(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trip_stop_actual_sequence CHECK (sequence_no > 0),
    CONSTRAINT ck_trip_stop_actual_time CHECK (
        actual_departure_at IS NULL OR actual_arrival_at IS NULL
        OR actual_departure_at >= actual_arrival_at
    )
);

CREATE TABLE trip_actual_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    version_no integer NOT NULL,
    actual_departure_at timestamptz NULL,
    actual_arrival_at timestamptz NULL,
    departure_odometer_km bigint NULL,
    arrival_odometer_km bigint NULL,
    actual_distance_km numeric(12,3) NULL,
    fuel_departure_l numeric(12,3) NULL,
    fuel_arrival_l numeric(12,3) NULL,
    snapshot jsonb NOT NULL,
    snapshot_schema_version integer NOT NULL,
    sha256 char(64) NOT NULL,
    previous_snapshot_id uuid NULL REFERENCES trip_actual_snapshots(id) ON DELETE RESTRICT,
    correction_case_id uuid NULL REFERENCES correction_cases(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid NULL,
    CONSTRAINT uq_trip_actual_snapshots_version UNIQUE (trip_id, version_no),
    CONSTRAINT uq_trip_actual_snapshots_trip_id UNIQUE (trip_id, id),
    CONSTRAINT fk_trip_actual_snapshots_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_actual_snapshots_actor FOREIGN KEY (company_id, created_by)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trip_snapshot_schema_version CHECK (snapshot_schema_version > 0)
);

ALTER TABLE trips
    ADD CONSTRAINT fk_trips_effective_snapshot
    FOREIGN KEY (id, effective_actual_snapshot_id)
    REFERENCES trip_actual_snapshots(trip_id, id) ON DELETE RESTRICT;

CREATE TABLE trip_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id uuid NOT NULL,
    trip_id uuid NOT NULL,
    event_type varchar(80) NOT NULL,
    occurred_at timestamptz NOT NULL,
    source varchar(30) NOT NULL,
    latitude numeric(9,6) NULL,
    longitude numeric(9,6) NULL,
    user_id uuid NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_trip_events_trip FOREIGN KEY (company_id, trip_id)
        REFERENCES trips(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_trip_events_user FOREIGN KEY (company_id, user_id)
        REFERENCES users(company_id, id) ON DELETE RESTRICT,
    CONSTRAINT ck_trip_events_latitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CONSTRAINT ck_trip_events_longitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);
CREATE INDEX ix_trip_events_timeline ON trip_events(company_id, trip_id, occurred_at);
CREATE INDEX ix_trip_events_company_time ON trip_events(company_id, occurred_at);
