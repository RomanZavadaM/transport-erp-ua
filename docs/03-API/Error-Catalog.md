# Каталог помилок API

Статус: **M0 freeze candidate**

`error.code` — стабільний технічний контракт. Текст `message` може локалізуватися і не використовується клієнтом для business branching.

## Загальні

| Code | HTTP | Значення |
|---|---:|---|
| `UNAUTHENTICATED` | 401 | Немає чинної автентифікації |
| `PERMISSION_DENIED` | 403 | Немає required permission |
| `ENTITY_NOT_FOUND` | 404 | Ресурс не існує або недоступний tenant scope |
| `VALIDATION_ERROR` | 422 | Domain/input validation |
| `CONCURRENT_MODIFICATION` | 409 | `If-Match` / row_version застарілий |
| `IDEMPOTENCY_KEY_REUSED` | 409 | Ключ повторно використаний з іншим request body |
| `INVALID_STATE_TRANSITION` | 409 | Команда недопустима в поточному state |
| `ENTITY_LOCKED` | 409 | Ресурс тимчасово недоступний для цієї mutation |
| `ENTITY_CLOSED` | 409 | Історичний об'єкт закритий і не редагується |
| `RATE_LIMITED` | 429 | Перевищено rate limit |

## Ресурсні конфлікти

| Code | HTTP | Значення |
|---|---:|---|
| `VEHICLE_TIME_CONFLICT` | 409 | Автобус має overlapping active assignment |
| `DRIVER_TIME_CONFLICT` | 409 | Водій має overlapping active assignment |
| `TRIP_ALREADY_ASSIGNED_TO_DUTY` | 409 | Trip уже входить до іншого active Duty |
| `VEHICLE_NOT_AVAILABLE` | 409 | Vehicle недоступний через lifecycle/operational state |
| `DRIVER_NOT_AVAILABLE` | 409 | Driver недоступний через employment/operational state |

Conflict details повинні містити ID конфліктної сутності та time period, якщо це не розкриває заборонені tenant data.

## Документи / compliance

| Code | HTTP | Значення |
|---|---:|---|
| `VEHICLE_DOCUMENT_REQUIRED` | 409 | Відсутній applicable required vehicle document |
| `VEHICLE_DOCUMENT_EXPIRED` | 409 | Applicable blocking document автобуса прострочений |
| `DRIVER_DOCUMENT_REQUIRED` | 409 | Відсутній applicable required driver document |
| `DRIVER_DOCUMENT_EXPIRED` | 409 | Applicable blocking document водія прострочений |
| `DOCUMENT_REVOKED` | 409 | Документ відкликаний |
| `COMPLIANCE_EVIDENCE_REQUIRED` | 409 | Відсутнє applicable carrier/route/other evidence, яке не є driver/vehicle document |
| `COMPLIANCE_RULE_NOT_APPLICABLE` | 409/422 | Команда намагається застосувати rule поза його context/effective period |

Requiredness визначається applicable versioned compliance rule, а не одним глобальним списком документів.

## Контролі

| Code | HTTP | Значення |
|---|---:|---|
| `MEDICAL_CHECK_REQUIRED` | 409 | Немає чинного required medical check |
| `MEDICAL_CHECK_FAILED` | 409 | Effective medical result = `UNFIT` |
| `MEDICAL_CHECK_EXPIRED` | 409 | Medical check втратив чинність |
| `TECHNICAL_CHECK_REQUIRED` | 409 | Немає чинного qualified technical check |
| `TECHNICAL_CHECK_FAILED` | 409 | Effective technical result негативний |
| `TECHNICAL_CHECK_EXPIRED` | 409 | Technical check втратив чинність |
| `DRIVER_PREDEPARTURE_CHECK_REQUIRED` | 409 | Немає required передвиїзного evidence перевірки технічного стану водієм |
| `DRIVER_PREDEPARTURE_CHECK_FAILED` | 409 | Передвиїзний check водія має blocking failure |
| `DRIVER_PREDEPARTURE_CHECK_SCOPE_DENIED` | 403 | Користувач не є assigned driver цього Duty або не має спеціального дозволу |
| `CHECK_ALREADY_COMPLETED` | 409 | Completed check не редагується |
| `CHECK_INVALIDATED` | 409 | Check визнаний недійсним |

## Дефекти / ремонти

| Code | HTTP | Значення |
|---|---:|---|
| `BLOCKING_DEFECT_EXISTS` | 409 | Є unresolved defect, що блокує Release |
| `ACTIVE_BLOCKING_REPAIR_EXISTS` | 409 | Є repair, що блокує operation |

## Release

| Code | HTTP | Значення |
|---|---:|---|
| `RELEASE_NOT_READY` | 409 | Один або більше blocking rules не PASS |
| `RELEASE_ALREADY_AUTHORIZED` | 409 | Positive authorization вже існує |
| `RELEASE_ALREADY_USED` | 409 | Фактичний виїзд уже використав release |
| `RELEASE_REEVALUATION_REQUIRED` | 409 | Ресурси/умови змінилися |

`RELEASE_NOT_READY.details` повинен містити список blocking rule codes, а не тільки текст.

## Waybill

| Code | HTTP | Значення |
|---|---:|---|
| `WAYBILL_PRIMARY_ALREADY_EXISTS` | 409 | Duty уже має non-cancelled `PRIMARY` Waybill за current enterprise policy |
| `WAYBILL_ALREADY_ISSUED` | 409 | Повторна issue-команда недопустима |
| `WAYBILL_ALREADY_CLOSED` | 409 | Closed document immutable |
| `WAYBILL_NUMBER_CONFLICT` | 409 | Business number collision; має бути практично недосяжним через DB constraint |
| `WAYBILL_NOT_READY_TO_CLOSE` | 409 | Missing required actual/final facts |
| `WAYBILL_CORRECTION_REQUIRED` | 409 | Зміна closed document можлива лише через correction |
| `WAYBILL_ROLE_NOT_ALLOWED` | 422 | `document_role` не дозволений deployment policy |

## Trip / Duty closing

| Code | HTTP | Значення |
|---|---:|---|
| `MISSING_ACTUAL_DATA` | 422/409 | Немає required fact для переходу |
| `INVALID_ACTUAL_TIME_RANGE` | 422 | Arrival/completion раніше departure |
| `INVALID_ODOMETER` | 422 | Odometer логічно некоректний |
| `DUTY_HAS_OPEN_TRIPS` | 409 | Duty не можна закрити |
| `UNRESOLVED_BLOCKING_EXCEPTION` | 409 | Є unresolved exception/case |

## Fuel

| Code | HTTP | Значення |
|---|---:|---|
| `INVALID_FUEL_QUANTITY` | 422 | Некоректна кількість |
| `FUEL_OPERATION_IMMUTABLE` | 409 | Historical operation не редагується silent update |
| `FUEL_REVERSAL_REQUIRED` | 409 | Потрібен reversal/correction workflow |

## Maintenance

| Code | HTTP | Значення |
|---|---:|---|
| `REPAIR_INVALID_STATE` | 409 | Repair command не дозволена state machine |
| `DEFECT_ALREADY_RESOLVED` | 409 | Повторне завершення defect |

## Формат details

```json
{
  "error": {
    "code": "VEHICLE_TIME_CONFLICT",
    "message": "Автобус уже призначений на інший наряд.",
    "details": {
      "vehicle_id": "uuid",
      "conflicting_duty_id": "uuid",
      "period": {
        "from": "2026-09-16T08:00:00+03:00",
        "to": "2026-09-16T12:00:00+03:00"
      }
    }
  },
  "meta": { "request_id": "uuid" }
}
```

## Правила розвитку

- existing code не змінює семантику silently;
- новий code документується тут і в OpenAPI contract/overlay;
- frontend handling ґрунтується на `code`;
- localized `message` не є частиною machine contract;
- internal exception/SQL text ніколи не віддається клієнту.
