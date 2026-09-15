# ERD v1 — TransportERP-UA

Статус: **M0 physical design draft**

Через розмір моделі ERD розділено на доменні фрагменти. Повний перелік таблиць: [Table Catalog](Table-Catalog.md).

## 1. Planning → Trip → Duty

```mermaid
erDiagram
    COMPANY ||--o{ DEPOT : має
    COMPANY ||--o{ STOP : має
    COMPANY ||--o{ ROUTE : має

    ROUTE ||--o{ ROUTE_VERSION : версіонується
    ROUTE_VERSION ||--o{ ROUTE_STOP : містить
    STOP ||--o{ ROUTE_STOP : використовується

    ROUTE ||--o{ SCHEDULE : має
    SCHEDULE ||--o{ SCHEDULE_VERSION : версіонується
    ROUTE_VERSION ||--o{ SCHEDULE_VERSION : фіксує
    SERVICE_CALENDAR ||--o{ SERVICE_CALENDAR_EXCEPTION : має
    SCHEDULE_VERSION ||--o{ SCHEDULE_RUN : містить
    SERVICE_CALENDAR ||--o{ SCHEDULE_RUN : керує
    SCHEDULE_RUN ||--o{ SCHEDULE_STOP_TIME : містить

    SCHEDULE_RUN ||--o{ TRIP : генерує
    ROUTE_VERSION ||--o{ TRIP : визначає
    TRIP ||--o{ TRIP_STOP_PLAN : snapshot
    TRIP ||--o| TRIP_ACTUAL : working_fact
    TRIP ||--o{ TRIP_ACTUAL_SNAPSHOT : immutable_fact
    TRIP ||--o{ TRIP_EVENT : timeline

    DUTY ||--o{ DUTY_TRIP : містить
    TRIP ||--o{ DUTY_TRIP : входить
```

## 2. Fleet / Drivers → Duty assignments

```mermaid
erDiagram
    COMPANY ||--o{ VEHICLE : має
    DEPOT ||--o{ VEHICLE : базує
    VEHICLE ||--o{ VEHICLE_DOCUMENT : має
    VEHICLE ||--o{ VEHICLE_ODOMETER_READING : має
    VEHICLE ||--o{ VEHICLE_STATUS_HISTORY : history

    COMPANY ||--o{ DRIVER : має
    DEPOT ||--o{ DRIVER : базує
    DRIVER ||--o{ DRIVER_DOCUMENT : має
    DRIVER ||--o{ DRIVER_STATUS_HISTORY : history

    DUTY ||--o{ DUTY_VEHICLE_ASSIGNMENT : plan
    VEHICLE ||--o{ DUTY_VEHICLE_ASSIGNMENT : assigned
    DUTY ||--o{ DUTY_DRIVER_ASSIGNMENT : plan
    DRIVER ||--o{ DUTY_DRIVER_ASSIGNMENT : assigned

    DUTY ||--o{ DUTY_VEHICLE_USAGE : fact
    VEHICLE ||--o{ DUTY_VEHICLE_USAGE : used
    DUTY ||--o{ DUTY_DRIVER_USAGE : fact
    DRIVER ||--o{ DUTY_DRIVER_USAGE : worked
    DUTY ||--o{ DUTY_EVENT : timeline
```

## 3. Duty → Release → Checks

```mermaid
erDiagram
    DUTY ||--|| RELEASE : має

    RELEASE ||--o{ PRE_TRIP_CHECK : перевіряється
    CHECK_TEMPLATE ||--o{ CHECK_TEMPLATE_ITEM : містить
    CHECK_TEMPLATE ||--o{ PRE_TRIP_CHECK : використаний
    PRE_TRIP_CHECK ||--o{ CHECK_RESULT : results
    CHECK_TEMPLATE_ITEM ||--o{ CHECK_RESULT : item

    PRE_TRIP_CHECK ||--o| MEDICAL_CHECK_DETAIL : medical
    DRIVER ||--o{ MEDICAL_CHECK_DETAIL : subject

    PRE_TRIP_CHECK ||--o| TECHNICAL_CHECK_DETAIL : technical
    VEHICLE ||--o{ TECHNICAL_CHECK_DETAIL : subject

    PRE_TRIP_CHECK ||--o| PRE_TRIP_CHECK_INVALIDATION : invalidated_by

    RELEASE ||--o{ RELEASE_RULE_EVALUATION : evaluates
    COMPLIANCE_RULE ||--o{ RELEASE_RULE_EVALUATION : rule
    RELEASE ||--o{ RELEASE_AUTHORIZATION : decision
```

## 4. Duty → Waybill → immutable versions

```mermaid
erDiagram
    DUTY ||--o| WAYBILL : документується
    WAYBILL ||--o{ WAYBILL_TRIP : містить
    TRIP ||--o{ WAYBILL_TRIP : включений

    DOCUMENT_TEMPLATE ||--o{ DOCUMENT_TEMPLATE_VERSION : версіонується
    WAYBILL ||--o{ WAYBILL_VERSION : версіонується
    DOCUMENT_TEMPLATE_VERSION ||--o{ WAYBILL_VERSION : render_template
    FILE ||--o{ WAYBILL_VERSION : pdf

    CORRECTION_CASE ||--o{ WAYBILL_VERSION : correction
    WAYBILL_VERSION ||--o| WAYBILL_VERSION : previous

    NUMBER_SEQUENCE ||--o{ WAYBILL : allocates
```

`NUMBER_SEQUENCE → WAYBILL` є логічним зв’язком нумерації; direct FK на sequence row може бути відсутнім, якщо snapshot series/year достатній. Якщо потрібна повна provenance — додати `number_sequence_id` до `waybills` у migration review.

## 5. Fleet → Fuel / Maintenance / Repairs

```mermaid
erDiagram
    VEHICLE ||--o{ FUEL_OPERATION : має
    DUTY ||--o{ FUEL_OPERATION : optional_context
    TRIP ||--o{ FUEL_OPERATION : optional_context
    WAYBILL ||--o{ FUEL_OPERATION : optional_context

    VEHICLE ||--o{ DEFECT : має
    PRE_TRIP_CHECK ||--o{ DEFECT : може_створити

    VEHICLE ||--o{ MAINTENANCE_PLAN : має
    MAINTENANCE_TYPE ||--o{ MAINTENANCE_PLAN : визначає
    MAINTENANCE_PLAN ||--o{ MAINTENANCE_EVENT : виконується
    VEHICLE ||--o{ MAINTENANCE_EVENT : history

    VEHICLE ||--o{ REPAIR_ORDER : ремонтується
    REPAIR_ORDER ||--o{ REPAIR_ORDER_ITEM : містить
```

## 6. Identity / Audit / System

```mermaid
erDiagram
    COMPANY ||--o{ USER : має
    USER ||--o{ USER_SESSION : sessions
    USER ||--o{ USER_ROLE : assigned
    ROLE ||--o{ USER_ROLE : contains
    ROLE ||--o{ ROLE_PERMISSION : has
    PERMISSION ||--o{ ROLE_PERMISSION : granted

    COMPANY ||--o{ AUDIT_LOG : audit
    USER ||--o{ AUDIT_LOG : actor
    COMPANY ||--o{ OUTBOX_EVENT : integration
    COMPANY ||--o{ REPORT_EXPORT : reports
    USER ||--o{ REPORT_EXPORT : requests
    FILE ||--o{ REPORT_EXPORT : artifact
    COMPANY ||--o{ SYSTEM_INTEGRITY_ALERT : monitors
```

## 7. Ключові cardinality/invariant notes

- один `Duty` містить 1..N `Trip` через `duty_trips`, але один Trip має максимум одне ACTIVE membership;
- один vehicle/driver може мати багато assignments у часі, але active periods не overlap завдяки exclusion constraint;
- один `Duty` має один `Release`;
- базова MVP policy: один чинний Waybill на Duty, але Waybill може містити багато Trips;
- completed check не переписується; invalidation окрема сутність;
- closed Trip має 1..N immutable actual snapshots, один із яких є effective;
- Waybill має 1..N immutable versions, одна current/effective;
- corrections не змінюють старі snapshot/version;
- audit та events append-only.

## 8. Polymorphic relations

Свідомо polymorphic без universal FK:

- `audit_log.entity_type/entity_id`;
- `outbox_events.aggregate_type/aggregate_id`;
- `correction_cases.entity_type/entity_id`;
- `entity_attachments.entity_type/entity_id`;
- `system_integrity_alerts.entity_type/entity_id`.

Усі вони зберігають `company_id`; domain/application layer перевіряє entity type + tenant scope. Там, де relation є критичною для integrity (Waybill PDF, Trip snapshot, release subject), використовується прямий FK.
