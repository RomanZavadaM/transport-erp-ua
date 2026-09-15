# PostgreSQL Schema — Duties, Assignments & Release

Статус: **M0 freeze-aligned physical design**

# Duties

## duties

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| depot_id | uuid | NULL |
| service_date | date | NOT NULL |
| duty_number | varchar(80) | NOT NULL |
| planned_start_at | timestamptz | NOT NULL |
| planned_end_at | timestamptz | NOT NULL |
| status | varchar(30) | NOT NULL |
| opened_at | timestamptz | NULL |
| opened_by | uuid | NULL |
| closed_at | timestamptz | NULL |
| closed_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |
| created_by | uuid | NULL |
| updated_at | timestamptz | NOT NULL |
| updated_by | uuid | NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(company_id,duty_number)`;
- CHECK planned_end_at > planned_start_at;
- CHECK status IN (`DRAFT`,`PLANNED`,`ASSIGNED`,`RELEASE_PENDING`,`BLOCKED`,`READY`,`AUTHORIZED`,`ON_LINE`,`RETURNED`,`CLOSING`,`CLOSED`,`CANCELLED`).

Indexes:

- `(company_id,service_date)`;
- `(company_id,status,service_date)`;
- `(company_id,depot_id,service_date)`.

`service_date` є explicit historical value і не переобчислюється після зміни company operational-day policy.

## duty_trips

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| trip_id | uuid | NOT NULL |
| sequence_no | integer | NOT NULL |
| membership_status | varchar(20) | NOT NULL |
| added_at | timestamptz | NOT NULL |
| added_by | uuid | NULL |
| removed_at | timestamptz | NULL |
| removed_by | uuid | NULL |
| reason | text | NULL |

Constraints:

- UNIQUE `(duty_id,sequence_no)` for active arrangement policy;
- partial UNIQUE `(trip_id)` WHERE membership_status='ACTIVE';
- CHECK membership_status IN (`ACTIVE`,`REMOVED`);
- CHECK sequence_no >0.

Фізичне видалення historical membership не використовується.

## duty_vehicle_assignments

Планове призначення автобуса.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| assignment_period | tstzrange | NOT NULL |
| assignment_status | varchar(20) | NOT NULL |
| assigned_at | timestamptz | NOT NULL |
| assigned_by | uuid | NULL |
| cancelled_at | timestamptz | NULL |
| cancelled_by | uuid | NULL |
| reason | text | NULL |

CHECK:

- NOT isempty(assignment_period);
- lower/upper bounds NOT NULL;
- status IN (`ACTIVE`,`CANCELLED`,`SUPERSEDED`).

Critical exclusion:

`EXCLUDE USING gist (company_id WITH =, vehicle_id WITH =, assignment_period WITH &&) WHERE assignment_status='ACTIVE'`.

MVP one-active-vehicle-at-a-time within Duty:

`EXCLUDE USING gist (duty_id WITH =, assignment_period WITH &&) WHERE assignment_status='ACTIVE'`.

Це дозволяє контрольовану заміну без overlap: A `[08:00,11:00)`, B `[11:00,18:00)`.

Indexes:

- `(company_id,duty_id)`;
- `(company_id,vehicle_id)` plus GiST exclusion index.

## duty_driver_assignments

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| driver_id | uuid | NOT NULL |
| assignment_role | varchar(30) | NOT NULL |
| crew_mode | varchar(20) | NOT NULL DEFAULT `SINGLE` |
| assignment_period | tstzrange | NOT NULL |
| assignment_status | varchar(20) | NOT NULL |
| assigned_at | timestamptz | NOT NULL |
| assigned_by | uuid | NULL |
| cancelled_at | timestamptz | NULL |
| cancelled_by | uuid | NULL |
| reason | text | NULL |

Critical exclusion:

`EXCLUDE USING gist (company_id WITH =, driver_id WITH =, assignment_period WITH &&) WHERE assignment_status='ACTIVE'`.

CHECK crew_mode IN (`SINGLE`,`CREW`).

Internal assignment roles:

- `PRIMARY`;
- `SECOND_DRIVER`;
- `RELIEF`;
- `TRAINEE` if approved by enterprise policy.

`crew_mode` є окремим regulatory/execution concept і не виводиться автоматично лише з `assignment_role`.

Не створюється нормативний constraint «рівно один PRIMARY на весь Duty». Global same-driver overlap protection діє незалежно від crew mode.

## duty_vehicle_usage

Фактичне використання автобуса, окремо від plan.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| actual_period | tstzrange | NOT NULL |
| source | varchar(30) | NOT NULL |
| started_event_id | uuid | NULL |
| ended_event_id | uuid | NULL |
| created_at | timestamptz | NOT NULL |

Historical row не перезаписує planned assignment. Period може бути закритий command-ом заміни/return; після Duty close usage history immutable.

## duty_driver_usage

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| driver_id | uuid | NOT NULL |
| usage_role | varchar(30) | NOT NULL |
| crew_mode | varchar(20) | NOT NULL DEFAULT `SINGLE` |
| actual_period | tstzrange | NOT NULL |
| source | varchar(30) | NOT NULL |
| created_at | timestamptz | NOT NULL |

CHECK crew_mode IN (`SINGLE`,`CREW`).

Використовується future worktime/payroll/compliance context як factual source. Crew mode може змінюватися між часовими usage segments одного Duty.

## duty_events

Append-only timeline.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| event_type | varchar(80) | NOT NULL |
| occurred_at | timestamptz | NOT NULL |
| source | varchar(30) | NOT NULL |
| payload | jsonb | NOT NULL DEFAULT `{}` |
| created_by | uuid | NULL |
| created_at | timestamptz | NOT NULL |

No UPDATE/DELETE runtime grants.

---

# Release

## releases

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| duty_id | uuid | NOT NULL |
| status | varchar(30) | NOT NULL |
| opened_at | timestamptz | NOT NULL |
| opened_by | uuid | NULL |
| evaluation_started_at | timestamptz | NULL |
| ready_at | timestamptz | NULL |
| authorized_at | timestamptz | NULL |
| authorized_by | uuid | NULL |
| actual_departure_at | timestamptz | NULL |
| blocked_code | varchar(100) | NULL |
| blocked_comment | text | NULL |
| created_at | timestamptz | NOT NULL |
| updated_at | timestamptz | NOT NULL |
| row_version | bigint | NOT NULL DEFAULT 1 |

Constraints:

- UNIQUE `(company_id,id)`;
- UNIQUE `(duty_id)`;
- CHECK status IN (`OPEN`,`WAITING_CHECKS`,`EVALUATING`,`BLOCKED`,`READY`,`AUTHORIZED`,`USED`).

Release один на Duty; нові checks/evaluations додаються до цього workflow.

## check_templates

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| check_type | varchar(40) | NOT NULL |
| name | text | NOT NULL |
| version_no | integer | NOT NULL |
| valid_period | daterange | NOT NULL |
| active | boolean | NOT NULL DEFAULT true |
| created_at | timestamptz | NOT NULL |

CHECK check_type IN (`MEDICAL`,`TECHNICAL`,`DRIVER_TECHNICAL_PREDEPARTURE`).

Versioned template не переписується після використання.

`DRIVER_TECHNICAL_PREDEPARTURE` фіксує окреме evidence обов'язкової передвиїзної перевірки технічного стану водієм і не підмінює qualified technical inspection.

## check_template_items

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| template_id | uuid | NOT NULL |
| code | varchar(80) | NOT NULL |
| sequence_no | integer | NOT NULL |
| label_key | varchar(160) | NOT NULL |
| value_type | varchar(30) | NOT NULL |
| required | boolean | NOT NULL |
| blocking_on_failure | boolean | NOT NULL DEFAULT false |
| configuration | jsonb | NOT NULL DEFAULT `{}` |

UNIQUE `(template_id,code)` і `(template_id,sequence_no)`.

`label_key`, а не hardcoded localized text, підтримує i18n.

## pre_trip_checks

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| release_id | uuid | NOT NULL |
| template_id | uuid | NULL |
| check_type | varchar(40) | NOT NULL |
| subject_type | varchar(30) | NOT NULL |
| subject_id | uuid | NOT NULL |
| status | varchar(20) | NOT NULL |
| started_at | timestamptz | NULL |
| completed_at | timestamptz | NULL |
| performed_by | uuid | NOT NULL |
| valid_until | timestamptz | NULL |
| comment | text | NULL |
| created_at | timestamptz | NOT NULL |

CHECK:

- check_type IN (`MEDICAL`,`TECHNICAL`,`DRIVER_TECHNICAL_PREDEPARTURE`);
- status IN (`PENDING`,`IN_PROGRESS`,`PASSED`,`FAILED`).

Після `PASSED/FAILED` row immutable для runtime update, окрім явно дозволеної technical metadata. Помилка в completed result виправляється invalidation + new check.

Actor rules:

- `MEDICAL` — користувач із `medical_check.perform`;
- `TECHNICAL` — qualified/authorized actor із `technical_check.perform`;
- `DRIVER_TECHNICAL_PREDEPARTURE` — assigned driver у власному Duty через dedicated permission/scope.

## medical_check_details

| Поле | Тип | Правила |
|---|---|---|
| pre_trip_check_id | uuid | PK/FK |
| company_id | uuid | NOT NULL |
| driver_id | uuid | NOT NULL |
| fitness_result | varchar(20) | NOT NULL |

CHECK fitness_result IN (`FIT`,`UNFIT`).

`UNFIT` є blocking result. `FIT_WITH_RESTRICTIONS` не входить у M0 щозмінний medical result set.

Не зберігати діагноз або зайві медичні дані без окремої підтвердженої потреби.

## technical_check_details

Деталі qualified technical inspection (`check_type=TECHNICAL`).

| Поле | Тип | Правила |
|---|---|---|
| pre_trip_check_id | uuid | PK/FK |
| company_id | uuid | NOT NULL |
| vehicle_id | uuid | NOT NULL |
| odometer_km | bigint | NOT NULL |
| result | varchar(20) | NOT NULL |
| blocking_defect_found | boolean | NOT NULL DEFAULT false |
| inspection_place | text | NULL |

CHECK odometer_km >=0; result IN (`PASSED`,`FAILED`).

Driver pre-departure check використовує `pre_trip_checks` + versioned `check_results`; він не створює другий qualified `technical_check_details` row.

## check_results

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| pre_trip_check_id | uuid | NOT NULL |
| template_item_id | uuid | NOT NULL |
| result_value | jsonb | NOT NULL |
| passed | boolean | NULL |
| comment | text | NULL |

UNIQUE `(pre_trip_check_id,template_item_id)`.

Backend derives final technical/driver-predeparture result from blocking items; frontend не задає довільно final PASS всупереч item results.

## pre_trip_check_invalidations

Separate evidence instead of rewriting original completed check.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| pre_trip_check_id | uuid | NOT NULL UNIQUE |
| reason | text | NOT NULL |
| invalidated_at | timestamptz | NOT NULL |
| invalidated_by | uuid | NOT NULL |
| replacement_check_id | uuid | NULL |

Original `PASSED/FAILED` row залишається історично незмінним.

## compliance_rules

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NULL/system or tenant |
| code | varchar(120) | NOT NULL |
| scope | varchar(50) | NOT NULL |
| severity | varchar(20) | NOT NULL |
| blocking | boolean | NOT NULL |
| valid_period | daterange | NOT NULL |
| applicability | jsonb | NOT NULL DEFAULT `{}` |
| configuration | jsonb | NOT NULL DEFAULT `{}` |
| active | boolean | NOT NULL DEFAULT true |

Stable `code` використовується audit/API/traceability.

`applicability` визначає transport/service/route context, для якого rule діє. Один global `required_for_release` seed не підмінює context-aware compliance evaluation.

Rule version/effective period забезпечує історичне відтворення Release decision.

## release_rule_evaluations

Append-only.

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| release_id | uuid | NOT NULL |
| evaluation_batch_id | uuid | NOT NULL |
| rule_id | uuid | NULL |
| rule_code | varchar(120) | NOT NULL |
| evaluated_at | timestamptz | NOT NULL |
| result | varchar(30) | NOT NULL |
| blocking | boolean | NOT NULL |
| subject_type | varchar(30) | NULL |
| subject_id | uuid | NULL |
| details | jsonb | NOT NULL DEFAULT `{}` |

CHECK result IN (`PASS`,`FAIL`,`WARNING`,`NOT_APPLICABLE`).

Unique batch/rule/subject composite as appropriate:

`UNIQUE(release_id,evaluation_batch_id,rule_code,subject_type,subject_id)` з NULL-safe strategy in concrete DDL.

No UPDATE/DELETE runtime grants.

## release_authorizations

| Поле | Тип | Правила |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | NOT NULL |
| release_id | uuid | NOT NULL |
| decision | varchar(20) | NOT NULL |
| authorized_at | timestamptz | NOT NULL |
| authorized_by | uuid | NOT NULL |
| comment | text | NULL |
| evaluation_batch_id | uuid | NULL |
| rule_evaluation_snapshot | jsonb | NOT NULL DEFAULT `{}` |
| created_at | timestamptz | NOT NULL |

CHECK decision IN (`AUTHORIZED`,`REJECTED`).

Partial UNIQUE `(release_id)` WHERE decision='AUTHORIZED'.

Позитивна авторизація може існувати лише одна; negative decisions можуть зберігатися як history відповідно до workflow.

Перед `AUTHORIZED` fresh evaluation знову перевіряє effective medical FIT, qualified technical check, driver pre-departure technical evidence, contextual documents, blocking defects/repairs та інші applicable rules.
