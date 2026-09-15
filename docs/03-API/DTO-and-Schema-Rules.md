# DTO та правила схем API

Статус: **M0 draft**

## 1. Загальні правила

- API не повертає ORM/database rows напряму;
- request/response DTO є окремими контрактами;
- read model може відрізнятися від write model;
- internal DB fields не потрапляють у API без явного рішення;
- sensitive fields мають permission-aware projections;
- `company_id` зазвичай не приймається від browser client, а визначається auth context;
- server-generated fields не дозволяються в create DTO.

## 2. Ідентифікатори

У зовнішньому API primary identifiers — UUID string.

Business identifiers (`trip_number`, `waybill_number`, `fleet_number`) не замінюють primary ID.

## 3. Версія агрегату

Mutable aggregate response містить:

- `row_version` у body за потреби;
- `ETag` header як canonical concurrency token.

Mutation DTO не містить поле `status`, якщо state змінюється command endpoint.

## 4. Create / Update separation

Приклад Vehicle:

`VehicleCreate`:

- depot_id;
- fleet_number;
- registration_number;
- vin optional;
- make;
- model;
- year;
- capacity;
- vehicle_type;
- fuel_type.

`VehicleUpdate` містить лише дозволені mutable master-data fields.

`lifecycle_status` не змінюється через generic update; для нього є commands.

## 5. Command DTO

Кожна business command має мінімальний explicit request DTO.

Наприклад `AssignVehicleCommand`:

```json
{
  "vehicle_id": "uuid",
  "from": "2026-09-16T05:30:00+03:00",
  "to": "2026-09-16T15:30:00+03:00"
}
```

`CancelTripCommand`:

```json
{
  "reason_code": "VEHICLE_UNAVAILABLE",
  "comment": "optional text"
}
```

`ReplaceVehicleCommand`:

```json
{
  "old_vehicle_id": "uuid",
  "new_vehicle_id": "uuid",
  "effective_at": "2026-09-16T10:22:00+03:00",
  "reason_code": "BREAKDOWN",
  "comment": "optional"
}
```

## 6. Release DTO

`ReleaseEvaluationResponse`:

```json
{
  "release_id": "uuid",
  "evaluation_batch_id": "uuid",
  "status": "BLOCKED",
  "rules": [
    {
      "code": "MEDICAL_CHECK_VALID",
      "result": "PASS",
      "blocking": true,
      "subject_type": "DRIVER",
      "subject_id": "uuid",
      "details": {}
    }
  ]
}
```

Frontend не обчислює final release state самостійно.

## 7. Medical / Technical DTO privacy

Medical response для диспетчера може бути projection:

```json
{
  "check_id": "uuid",
  "driver_id": "uuid",
  "result": "FIT",
  "completed_at": "...",
  "valid_until": "...",
  "effective": true
}
```

Без непотрібних internal/medical details.

Медик із відповідним permission отримує розширену projection.

## 8. Waybill DTO

`WaybillRead` містить:

- id;
- full_number;
- duty_id;
- status;
- issued_at/returned_at/closed_at;
- current_version;
- pdf availability;
- row_version для mutable lifecycle phase.

`WaybillVersionRead`:

- id;
- version_no;
- template_version_id;
- snapshot_schema_version;
- snapshot_sha256;
- pdf_sha256;
- created_at/by;
- previous_version_id;
- correction_case_id/reason where allowed.

Snapshot JSON не обов'язково повертається в list endpoint.

## 9. Trip / Duty list projections

List endpoint не повертає повний aggregate graph.

`DutyListItem` може містити:

- id;
- duty_number;
- service_date;
- planned_start/end;
- status;
- assigned vehicle summary;
- assigned driver summaries;
- release summary;
- waybill summary;
- problem indicators;
- row_version.

Detail endpoint повертає розширений DTO.

## 10. Date/time

- instant → RFC3339/ISO-8601 з offset;
- date → `YYYY-MM-DD`;
- time-of-day → `HH:MM:SS`;
- range DTO завжди `{from,to}`;
- `to > from` валідовується server-side.

## 11. Numeric data

- money — decimal/string-safe representation відповідно до OpenAPI schema; не binary float у DB;
- fuel liters — decimal;
- distance — decimal;
- odometer — integer kilometers для MVP, якщо не буде окремо затверджена точність до 0.1 км.

## 12. Nullability

`null` використовується лише коли поле семантично може бути відсутнім.

Не використовувати `""`, `0` або fake UUID як заміну null.

## 13. Enums / codes

Technical values стабільні та англомовні:

- `ACTIVE`;
- `CLOSED`;
- `AUTHORIZED`;
- `VEHICLE_TIME_CONFLICT`.

Presentation layer відображає локалізований label.

## 14. Collection filtering

Filter parameters мають явні OpenAPI types.

Не підтримується arbitrary SQL-like filter expression від клієнта.

Sort — whitelist fields; unknown sort повертає validation error.

## 15. Partial response / expansion

MVP не вводить універсальний GraphQL-like `expand=*`.

Для складних projection створюються чіткі endpoints (`/timeline`, `/assignments`, `/versions`).

## 16. Compatibility

Додавання optional response field — backward-compatible.

Видалення/rename field, зміна типу або semantics — breaking change і потребує versioning/deprecation рішення.

## 17. Pydantic/OpenAPI mapping

При реалізації Pydantic models повинні бути похідними від цього contract, а не навпаки. Generated OpenAPI перевіряється contract tests проти затвердженої schema.