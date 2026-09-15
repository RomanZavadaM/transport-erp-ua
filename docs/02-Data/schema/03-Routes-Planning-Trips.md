# PostgreSQL Schema — Routes, Planning & Trips

# Stops / Routes

## stops

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| code | varchar(40) | NOT NULL |
| name | text | NOT NULL |
| latitude | numeric(9,6) | NULL |
| longitude | numeric(9,6) | NULL |
| address | text | NULL |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(company_id,code)`;
- coordinate range CHECKs where not null.

## routes

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| route_number | varchar(30) | NOT NULL |
| name | text | NOT NULL |
| route_type | varchar(40) | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(company_id,route_number)`.

`route_number` є varchar, не integer (`12A`, `7-Т` тощо).

## route_versions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| route_id | uuid | NOT NULL |
| version_no | integer | NOT NULL |
| valid_period | daterange | NOT NULL |
| public_name | text | NULL |
| planned_distance_km | numeric(12,3) | NULL |
| status | varchar(20) | NOT NULL |
| metadata | jsonb | NOT NULL DEFAULT `{}` |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(route_id,version_no)`;
- CHECK NOT isempty(valid_period);
- CHECK `status IN ('DRAFT','ACTIVE','RETIRED')`;
- CHECK planned_distance_km IS NULL OR planned_distance_km >= 0;
- EXCLUDE USING gist `(route_id WITH =, valid_period WITH &&)` WHERE status='ACTIVE'.

Used version після activation/history usage не редагується in-place; зміна структури маршруту = new version.

## route_stops

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| route_version_id | uuid | NOT NULL |
| direction | smallint | NOT NULL |
| sequence_no | integer | NOT NULL |
| stop_id | uuid | NOT NULL |
| distance_from_start_km | numeric(12,3) | NOT NULL |
| planned_travel_seconds | integer | NULL |
| planned_dwell_seconds | integer | NULL |

Constraints:

- UNIQUE `(route_version_id,direction,sequence_no)`;
- CHECK sequence_no > 0;
- CHECK direction >= 0;
- CHECK distance_from_start_km >= 0;
- CHECK planned_* IS NULL OR >=0.

Tenant-aware FKs to route_versions and stops.

Index `(route_version_id,direction,sequence_no)`.

---

# Schedules

## schedules

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| route_id | uuid | NOT NULL |
| code | varchar(50) | NOT NULL |
| name | text | NOT NULL |
| status | varchar(20) | NOT NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

UNIQUE `(company_id,code)`.

## schedule_versions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| schedule_id | uuid | NOT NULL |
| version_no | integer | NOT NULL |
| route_version_id | uuid | NOT NULL |
| valid_period | daterange | NOT NULL |
| status | varchar(20) | NOT NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Constraints:

- UNIQUE `(schedule_id,version_no)`;
- CHECK NOT isempty(valid_period);
- CHECK status IN (`DRAFT`,`ACTIVE`,`RETIRED`);
- exclusion same schedule + overlapping ACTIVE valid_period.

`route_version_id` фіксує конкретну версію маршруту, а не плаваючий current route.

## service_calendars

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| name | text | NOT NULL |
| monday | boolean | NOT NULL |
| tuesday | boolean | NOT NULL |
| wednesday | boolean | NOT NULL |
| thursday | boolean | NOT NULL |
| friday | boolean | NOT NULL |
| saturday | boolean | NOT NULL |
| sunday | boolean | NOT NULL |
| valid_period | daterange | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |

CHECK NOT isempty(valid_period).

## service_calendar_exceptions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| service_calendar_id | uuid | NOT NULL |
| service_date | date | NOT NULL |
| operation | varchar(10) | NOT NULL |
| comment | text | NULL |

Constraints:

- UNIQUE `(service_calendar_id,service_date)`;
- CHECK operation IN (`ADD`,`REMOVE`).

## schedule_runs

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| schedule_version_id | uuid | NOT NULL |
| service_calendar_id | uuid | NOT NULL |
| run_code | varchar(50) | NOT NULL |
| direction | smallint | NOT NULL |
| departure_time | time | NOT NULL |
| arrival_time | time | NOT NULL |
| arrival_day_offset | smallint | NOT NULL DEFAULT 0 |
| active | boolean | NOT NULL DEFAULT true |

Constraints:

- UNIQUE `(schedule_version_id,run_code)`;
- CHECK arrival_day_offset >= 0;
- CHECK direction >=0.

## schedule_stop_times

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| schedule_run_id | uuid | NOT NULL |
| route_stop_id | uuid | NOT NULL |
| sequence_no | integer | NOT NULL |
| arrival_offset_seconds | integer | NULL |
| departure_offset_seconds | integer | NULL |

Constraints:

- UNIQUE `(schedule_run_id,sequence_no)`;
- CHECK sequence_no >0;
- CHECK offsets IS NULL OR >=0.

---

# Trips

## trips

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| service_date | date | NOT NULL |
| schedule_run_id | uuid | NULL |
| route_version_id | uuid | NOT NULL |
| trip_number | varchar(80) | NULL |
| planned_departure_at | timestamptz | NOT NULL |
| planned_arrival_at | timestamptz | NOT NULL |
| status | varchar(30) | NOT NULL |
| cancel_reason_code | varchar(80) | NULL |
| cancel_comment | text | NULL |
| effective_actual_snapshot_id | uuid | NULL |
| closed_at | timestamptz | NULL |
| closed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- partial UNIQUE `(schedule_run_id,service_date)` WHERE schedule_run_id IS NOT NULL;
- CHECK planned_arrival_at > planned_departure_at;
- CHECK status IN (`DRAFT`,`PLANNED`,`SCHEDULED`,`READY`,`RELEASED`,`IN_PROGRESS`,`COMPLETED`,`CLOSED`,`CANCELLED`).

Indexes:

- `(company_id,service_date)`;
- `(company_id,status,service_date)`;
- `(route_version_id,service_date)`;
- `(planned_departure_at)`;
- `(schedule_run_id,service_date)`.

`service_date` зберігається окремо від timestamp date, бо overnight trip може належати попередньому operational day.

## trip_stop_plan

Snapshot плану зупинок на момент створення рейсу.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| stop_id | uuid | NOT NULL |
| route_stop_id | uuid | NULL |
| sequence_no | integer | NOT NULL |
| planned_arrival_at | timestamptz | NULL |
| planned_departure_at | timestamptz | NULL |

UNIQUE `(trip_id,sequence_no)`.

Historical plan не змінюється через новий schedule version.

## trip_actuals

Mutable working facts лише до close.

| Поле | Тип | Правила |
|---|---|---|
| trip_id | uuid | PK |
| company_id | uuid | NOT NULL |
| actual_departure_at | timestamptz | NULL |
| actual_arrival_at | timestamptz | NULL |
| departure_odometer_km | bigint | NULL |
| arrival_odometer_km | bigint | NULL |
| actual_distance_km | numeric(12,3) | NULL |
| fuel_departure_l | numeric(12,3) | NULL |
| fuel_arrival_l | numeric(12,3) | NULL |
| origin_source | varchar(30) | NOT NULL DEFAULT `MANUAL` |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

CHECK arrival_odometer IS NULL OR departure_odometer IS NULL OR arrival_odometer >= departure_odometer.

CHECK actual_arrival_at IS NULL OR actual_departure_at IS NULL OR actual_arrival_at >= actual_departure_at.

## trip_stop_actuals

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| stop_id | uuid | NOT NULL |
| sequence_no | integer | NOT NULL |
| actual_arrival_at | timestamptz | NULL |
| actual_departure_at | timestamptz | NULL |
| source | varchar(30) | NOT NULL |

UNIQUE `(trip_id,sequence_no)` for effective current actual row in MVP model.

## trip_actual_snapshots

Immutable snapshot created at close/correction.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| version_no | integer | NOT NULL |
| actual_departure_at | timestamptz | NULL |
| actual_arrival_at | timestamptz | NULL |
| departure_odometer_km | bigint | NULL |
| arrival_odometer_km | bigint | NULL |
| actual_distance_km | numeric(12,3) | NULL |
| fuel_departure_l | numeric(12,3) | NULL |
| fuel_arrival_l | numeric(12,3) | NULL |
| snapshot | jsonb | NOT NULL |
| snapshot_schema_version | integer | NOT NULL |
| sha256 | char(64) | NOT NULL |
| previous_snapshot_id | uuid | NULL self-FK |
| correction_case_id | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

UNIQUE `(trip_id,version_no)`.

No UPDATE/DELETE runtime grants.

`trips.effective_actual_snapshot_id` FK додається на цю table, із перевіркою належності snapshot тому самому trip через composite design/trigger as appropriate.

## trip_events

Append-only operational timeline.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| event_type | varchar(80) | NOT NULL |
| occurred_at | timestamptz | NOT NULL |
| source | varchar(30) | NOT NULL |
| latitude | numeric(9,6) | NULL |
| longitude | numeric(9,6) | NULL |
| user_id | uuid | NULL |
| payload | jsonb | NOT NULL DEFAULT `{}` |
| created_at | timestamptz | NOT NULL |

Indexes:

- `(company_id,trip_id,occurred_at)`;
- `(company_id,occurred_at)`.

No UPDATE/DELETE runtime grants. GPS high-volume positions у майбутньому не пишуться сюди як кожна координата; для них буде окрема partitioned domain table.