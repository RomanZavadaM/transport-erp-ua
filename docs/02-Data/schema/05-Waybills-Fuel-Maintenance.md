# PostgreSQL Schema — Waybills, Fuel, Maintenance & Corrections

Статус: **M0 freeze-aligned physical design**

# Documents / Waybills

## number_sequences

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| document_type | varchar(60) | NOT NULL |
| series | varchar(30) | NOT NULL |
| year | integer | NOT NULL |
| prefix | varchar(30) | NULL |
| suffix | varchar(30) | NULL |
| next_value | bigint | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,document_type,series,year)`;
- CHECK next_value > 0.

Number allocation тільки під row lock; `MAX(number)+1` заборонено.

Формат/скидання нумерації є enterprise policy. Уже виданий номер ніколи не reuse-иться. Рекомендований deployment default — серія за типом документа/роком, якщо підприємство не затвердить іншу policy.

## document_templates

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| document_type | varchar(60) | NOT NULL |
| code | varchar(80) | NOT NULL |
| name | text | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |

Stable code + locale/version-specific child.

## document_template_versions

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| template_id | uuid | NOT NULL |
| version_no | integer | NOT NULL |
| locale | varchar(5) | NOT NULL |
| valid_period | daterange | NOT NULL |
| html_template | text | NOT NULL |
| css_template | text | NOT NULL |
| input_schema | jsonb | NOT NULL |
| engine | varchar(40) | NOT NULL DEFAULT `HTML_PDF` |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Constraints:

- UNIQUE `(template_id,version_no,locale)`;
- CHECK locale IN (`uk`,`en`,`es`,`fr`,`de`);
- CHECK NOT isempty(valid_period).

Used template version immutable.

## waybills

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| document_role | varchar(40) | NOT NULL DEFAULT `PRIMARY` |
| series | varchar(30) | NOT NULL |
| number | bigint | NOT NULL |
| full_number | varchar(100) | NOT NULL |
| status | varchar(30) | NOT NULL |
| current_version_id | uuid | NULL |
| issued_at | timestamptz | NULL |
| issued_by | uuid | NULL |
| returned_at | timestamptz | NULL |
| closed_at | timestamptz | NULL |
| closed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(company_id,full_number)`;
- CHECK char_length(document_role) > 0;
- CHECK status IN (`DRAFT`,`GENERATED`,`ISSUED`,`ACTIVE`,`RETURNED`,`CLOSING`,`CLOSED`,`CANCELLED`).

M0 enterprise default policy: максимум один non-cancelled `PRIMARY` Waybill на Duty:

`UNIQUE (duty_id) WHERE document_role='PRIMARY' AND status <> 'CANCELLED'`.

Це не забороняє майбутні explicit supplementary document roles. Новий role не потребує перепроєктування Waybill aggregate. Correction є новою `waybill_version`, а не другим незалежним `PRIMARY` Waybill.

Waybill є enterprise operational/accounting document; requiredness і role policy визначаються deployment/compliance configuration, якщо specific applicable rule не встановлює інше.

No DELETE closed document.

## waybill_trips

| Поле | Тип | Правила |
|---|---|---|
| waybill_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| company_id | uuid | NOT NULL |
| sequence_no | integer | NOT NULL |

PK `(waybill_id,trip_id)`.

UNIQUE `(waybill_id,sequence_no)`.

Дозволяє 1 Waybill → N Trips.

## waybill_versions

Immutable document history.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| waybill_id | uuid | NOT NULL |
| version_no | integer | NOT NULL |
| document_template_version_id | uuid | NOT NULL |
| snapshot | jsonb | NOT NULL |
| snapshot_schema_version | integer | NOT NULL |
| snapshot_sha256 | char(64) | NOT NULL |
| pdf_file_id | uuid | NULL |
| pdf_sha256 | char(64) | NULL |
| generation_status | varchar(20) | NOT NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| previous_version_id | uuid | NULL self-FK |
| correction_case_id | uuid | NULL |
| correction_reason | text | NULL |

Constraints:

- UNIQUE `(waybill_id,version_no)`;
- CHECK generation_status IN (`PENDING`,`READY`,`FAILED`).

No runtime UPDATE/DELETE після version finalized; generation metadata transition PENDING→READY/FAILED має бути окремо чітко дозволена або винесена в job table, щоб snapshot/content залишалися immutable.

`waybills.current_version_id` повинен посилатися на version того самого waybill; concrete composite FK/constraint реалізується в migration design.

Historical version зберігає explicit template version/locale через `document_template_version_id`; зміна user locale не regenerates historical PDF.

---

# Files

## files

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| storage_provider | varchar(30) | NOT NULL |
| storage_key | text | NOT NULL |
| original_filename | text | NOT NULL |
| mime_type | varchar(120) | NOT NULL |
| size_bytes | bigint | NOT NULL |
| sha256 | char(64) | NOT NULL |
| retention_class | varchar(60) | NULL |
| retain_until | date | NULL |
| legal_hold | boolean | NOT NULL DEFAULT false |
| retention_metadata | jsonb | NOT NULL DEFAULT `{}` |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Constraints:

- UNIQUE `(storage_provider,storage_key)`;
- CHECK size_bytes >=0.

Binary bytes не зберігаються в PostgreSQL; storage S3-compatible/MinIO.

Retention policy class-based:

- один global `retention_days` не використовується;
- `retain_until` може бути продовжений policy/legal hold workflow;
- application purge не видаляє object при `legal_hold=true` або до `retain_until`;
- CLOSED Waybill/history не auto-purge-иться лише через досягнення мінімального строку;
- final object-lock duration походить із затвердженої enterprise retention matrix.

## entity_attachments

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| entity_type | varchar(60) | NOT NULL |
| entity_id | uuid | NOT NULL |
| file_id | uuid | NOT NULL |
| attachment_type | varchar(60) | NOT NULL |
| description | text | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |

Polymorphic `entity_id` не має універсального FK; допустимі entity_type контролюються application/domain layer. Для core document relation використовувати прямий FK (`pdf_file_id`) замість polymorphic link.

---

# Fuel

## fuel_operations

Append/ledger-like history.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| duty_id | uuid | NULL |
| trip_id | uuid | NULL |
| waybill_id | uuid | NULL |
| operation_type | varchar(30) | NOT NULL |
| fuel_type_id | uuid | NOT NULL |
| quantity_l | numeric(12,3) | NOT NULL |
| unit_price | numeric(14,4) | NULL |
| amount | numeric(14,2) | NULL |
| odometer_km | bigint | NULL |
| operation_at | timestamptz | NOT NULL |
| document_number | varchar(100) | NULL |
| source | varchar(30) | NOT NULL |
| reversal_of_id | uuid | NULL self-FK |
| created_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |

CHECK:

- quantity_l >0;
- odometer_km IS NULL OR >=0;
- operation_type IN (`REFUEL`,`ISSUE`,`RETURN`,`CONSUMPTION`,`ADJUSTMENT`,`REVERSAL`).

Indexes:

- `(company_id,vehicle_id,operation_at)`;
- `(company_id,operation_at)`;
- `(duty_id)`;
- `(waybill_id)`.

Historical operation не silent UPDATE-иться; correction через reversal/new operation.

---

# Defects / Maintenance

## defects

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| reported_at | timestamptz | NOT NULL |
| reported_by | uuid | NULL |
| source | varchar(30) | NOT NULL |
| trip_id | uuid | NULL |
| duty_id | uuid | NULL |
| technical_check_id | uuid | NULL |
| severity | varchar(20) | NOT NULL |
| description | text | NOT NULL |
| blocks_release | boolean | NOT NULL DEFAULT false |
| status | varchar(30) | NOT NULL |
| resolved_at | timestamptz | NULL |
| resolved_by | uuid | NULL |
| resolution_comment | text | NULL |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

CHECK status IN (`OPEN`,`ACKNOWLEDGED`,`IN_REPAIR`,`RESOLVED`,`CLOSED`).

Indexes:

- `(company_id,vehicle_id,status)`;
- partial `(vehicle_id)` WHERE blocks_release=true AND status NOT IN (`RESOLVED`,`CLOSED`).

## maintenance_types

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| code | varchar(60) | NOT NULL |
| name | text | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |

## maintenance_plans

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| maintenance_type_id | uuid | NOT NULL |
| interval_km | bigint | NULL |
| interval_days | integer | NULL |
| last_completed_date | date | NULL |
| last_completed_odometer | bigint | NULL |
| next_due_date | date | NULL |
| next_due_odometer | bigint | NULL |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

CHECK:

- interval_km IS NULL OR interval_km >0;
- interval_days IS NULL OR interval_days >0;
- at least one interval criterion should be present according to policy.

## maintenance_events

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| maintenance_plan_id | uuid | NULL |
| status | varchar(20) | NOT NULL |
| opened_at | timestamptz | NOT NULL |
| started_at | timestamptz | NULL |
| completed_at | timestamptz | NULL |
| odometer_km | bigint | NULL |
| provider | text | NULL |
| cost | numeric(14,2) | NULL |
| comment | text | NULL |
| created_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Exact maintenance state machine may be simpler than repair; minimum statuses (`OPEN`,`IN_PROGRESS`,`COMPLETED`,`CANCELLED`).

## repair_orders

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| number | varchar(80) | NOT NULL |
| status | varchar(30) | NOT NULL |
| blocks_operation | boolean | NOT NULL DEFAULT false |
| opened_at | timestamptz | NOT NULL |
| opened_by | uuid | NOT NULL |
| planned_start | timestamptz | NULL |
| actual_start | timestamptz | NULL |
| actual_finish | timestamptz | NULL |
| odometer_km | bigint | NULL |
| description | text | NOT NULL |
| total_cost | numeric(14,2) | NULL |
| closed_at | timestamptz | NULL |
| closed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,number)`;
- CHECK status IN (`OPEN`,`DIAGNOSIS`,`APPROVED`,`IN_PROGRESS`,`WAITING_PARTS`,`COMPLETED`,`VERIFIED`,`CLOSED`,`CANCELLED`).

Partial index:

`(vehicle_id) WHERE blocks_operation=true AND status NOT IN ('CLOSED','CANCELLED')`.

## repair_order_items

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| repair_order_id | uuid | NOT NULL |
| item_type | varchar(30) | NOT NULL |
| description | text | NOT NULL |
| part_number | varchar(100) | NULL |
| quantity | numeric(12,3) | NOT NULL |
| unit | varchar(20) | NOT NULL |
| unit_price | numeric(14,4) | NULL |
| amount | numeric(14,2) | NULL |

CHECK quantity >0.

---

# Corrections

## correction_cases

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| entity_type | varchar(60) | NOT NULL |
| entity_id | uuid | NOT NULL |
| reason_code | varchar(80) | NOT NULL |
| reason | text | NOT NULL |
| status | varchar(20) | NOT NULL |
| requested_at | timestamptz | NOT NULL |
| requested_by | uuid | NOT NULL |
| approved_at | timestamptz | NULL |
| approved_by | uuid | NULL |
| completed_at | timestamptz | NULL |
| completed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

CHECK status IN (`OPEN`,`APPROVED`,`REJECTED`,`COMPLETED`,`CANCELLED`).

Correction case сам не переписує history; він авторизує створення new immutable snapshot/version.

Indexes:

- `(company_id,entity_type,entity_id)`;
- `(company_id,status,requested_at)`.
