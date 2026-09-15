# PostgreSQL Schema — Fleet & Drivers

## vehicle_types

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL for global/system type |
| code | varchar(50) | NOT NULL |
| name | text | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |

Unique tenant/system code policy через partial indexes.

## fuel_types

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL for global/system |
| code | varchar(30) | NOT NULL |
| name | text | NOT NULL |
| unit | varchar(10) | NOT NULL DEFAULT `L` |
| active | boolean | NOT NULL DEFAULT true |

## vehicles

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| depot_id | uuid | NULL |
| fleet_number | varchar(30) | NOT NULL |
| registration_number | varchar(20) | NOT NULL |
| vin | varchar(32) | NULL |
| make | varchar(80) | NOT NULL |
| model | varchar(80) | NOT NULL |
| year | smallint | NULL |
| vehicle_type_id | uuid | NULL |
| fuel_type_id | uuid | NULL |
| seats | smallint | NULL |
| capacity_total | smallint | NULL |
| lifecycle_status | varchar(30) | NOT NULL |
| commissioned_at | date | NULL |
| decommissioned_at | date | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id, id)`;
- UNIQUE `(company_id, fleet_number)`;
- UNIQUE `(company_id, registration_number)`;
- UNIQUE VIN WHERE vin IS NOT NULL;
- CHECK `lifecycle_status IN ('ACTIVE','SUSPENDED','REPAIR','DECOMMISSIONED')`;
- CHECK year IS NULL OR year BETWEEN 1950 AND 2100;
- CHECK seats IS NULL OR seats >= 0;
- CHECK capacity_total IS NULL OR capacity_total >= 0;
- CHECK seats IS NULL OR capacity_total IS NULL OR capacity_total >= seats;
- CHECK decommissioned_at IS NULL OR commissioned_at IS NULL OR decommissioned_at >= commissioned_at.

Composite FK `(company_id,depot_id)` → depots when depot_id not null.

Indexes:

- `(company_id,lifecycle_status)`;
- `(company_id,depot_id,lifecycle_status)`;
- registration/fleet unique indexes cover common lookups.

## vehicle_status_history

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| status | varchar(30) | NOT NULL |
| valid_from | timestamptz | NOT NULL |
| valid_to | timestamptz | NULL |
| reason_code | varchar(80) | NULL |
| reason | text | NULL |
| changed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |

FK `(company_id,vehicle_id)` → vehicles.

Історія не видаляється. Один open period policy забезпечується application + partial unique/index або exclusion design при реалізації.

## vehicle_runtime_state

Projection, не historical source of truth.

| Поле | Тип | Правила |
|---|---|---|
| vehicle_id | uuid | PK/FK vehicles |
| company_id | uuid | NOT NULL |
| last_confirmed_odometer_km | bigint | NULL |
| last_odometer_at | timestamptz | NULL |
| current_duty_id | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Може бути відновлена з history tables.

## vehicle_document_types

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| code | varchar(80) | NOT NULL |
| name | text | NOT NULL |
| required_for_release | boolean | NOT NULL DEFAULT false |
| blocks_release_if_expired | boolean | NOT NULL DEFAULT false |
| warning_days | integer | NULL |
| active | boolean | NOT NULL DEFAULT true |

CHECK warning_days IS NULL OR warning_days >= 0.

## vehicle_documents

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| document_type_id | uuid | NOT NULL |
| series | varchar(30) | NULL |
| number | varchar(100) | NOT NULL |
| issued_at | date | NULL |
| valid_from | date | NULL |
| valid_until | date | NULL |
| issuer | text | NULL |
| status | varchar(30) | NOT NULL |
| file_id | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Constraints:

- CHECK valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from;
- CHECK status IN (`ACTIVE`,`REVOKED`,`SUPERSEDED`); `EXPIRED` краще derive by date, а не вручну зберігати як єдину істину.

Indexes:

- `(company_id,vehicle_id,document_type_id)`;
- `(company_id,valid_until)`;
- partial `(vehicle_id,document_type_id,valid_until)` WHERE status='ACTIVE'.

При продовженні/оновленні створюється новий document row; старий може стати `SUPERSEDED`, але не переписується.

## vehicle_odometer_readings

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| recorded_at | timestamptz | NOT NULL |
| odometer_km | bigint | NOT NULL |
| confirmed | boolean | NOT NULL DEFAULT true |
| source | varchar(30) | NOT NULL |
| trip_id | uuid | NULL |
| duty_id | uuid | NULL |
| waybill_id | uuid | NULL |
| correction_of_id | uuid | NULL self-FK |
| recorded_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |

CHECK odometer_km >= 0.

`source IN ('MANUAL','WAYBILL','TRIP','TECH_CHECK','GPS','IMPORT','CORRECTION')`.

Indexes:

- `(company_id,vehicle_id,recorded_at DESC)`;
- partial `(vehicle_id,recorded_at DESC)` WHERE confirmed=true.

Monotonic current odometer перевіряється в transaction із lock `vehicle_runtime_state`; historical correction не виконується silent UPDATE.

---

# Drivers

## drivers

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| default_depot_id | uuid | NULL |
| personnel_number | varchar(30) | NOT NULL |
| last_name | varchar(100) | NOT NULL |
| first_name | varchar(100) | NOT NULL |
| middle_name | varchar(100) | NULL |
| birth_date | date | NULL |
| phone | varchar(40) | NULL |
| employment_status | varchar(30) | NOT NULL |
| hire_date | date | NULL |
| dismissal_date | date | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(company_id,personnel_number)`;
- CHECK `employment_status IN ('ACTIVE','LEAVE','SICK','SUSPENDED','TERMINATED')`;
- CHECK dismissal_date IS NULL OR hire_date IS NULL OR dismissal_date >= hire_date.

Indexes:

- `(company_id,employment_status)`;
- `(company_id,default_depot_id,employment_status)`;
- optional name search index determined after production query profiling.

## driver_status_history

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| driver_id | uuid | NOT NULL |
| status | varchar(30) | NOT NULL |
| valid_from | timestamptz | NOT NULL |
| valid_to | timestamptz | NULL |
| reason_code | varchar(80) | NULL |
| reason | text | NULL |
| changed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |

Append-only history.

## driver_document_types

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| code | varchar(80) | NOT NULL |
| name | text | NOT NULL |
| required_for_release | boolean | NOT NULL DEFAULT false |
| blocks_release_if_expired | boolean | NOT NULL DEFAULT false |
| warning_days | integer | NULL |
| active | boolean | NOT NULL DEFAULT true |

Типи можуть включати license/category/qualification, але exact regulatory catalog затверджується в legal review.

## driver_documents

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| driver_id | uuid | NOT NULL |
| document_type_id | uuid | NOT NULL |
| series | varchar(30) | NULL |
| number | varchar(100) | NOT NULL |
| issued_at | date | NULL |
| valid_from | date | NULL |
| valid_until | date | NULL |
| issuer | text | NULL |
| status | varchar(30) | NOT NULL |
| file_id | uuid | NULL |
| metadata | jsonb | NOT NULL DEFAULT `{}` |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Indexes:

- `(company_id,driver_id,document_type_id)`;
- `(company_id,valid_until)`;
- partial active document index.

`metadata` дозволяє зберігати category-specific structured attributes до моменту, коли конкретне поле виправдано винести в нормалізовану таблицю. Required release facts не повинні залежати від довільного UI JSON parsing.

## user-driver link

Після створення `drivers` додається tenant-aware FK:

`users(company_id, driver_id) → drivers(company_id,id)`.

Один driver може мати zero/one user account за MVP policy. Якщо майбутня identity модель вимагатиме many accounts/identity providers, зв'язок буде винесено в association table через migration.