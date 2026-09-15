# OpenAPI MVP Contract

Статус: **M0 / Architecture Freeze draft**  
Пов’язаний issue: **#2**  
Канонічна мова: **українська**

## 1. Принцип API

API версіонується під `/api/v1` і поділяє:

- **queries** — `GET` для читання;
- **commands** — явні `POST` для бізнес-переходів;
- **limited PATCH** — лише для безпечних mutable master-data полів.

Заборонений анти-патерн:

`PATCH /trips/{id} { "status": "CLOSED" }`

Правильно:

`POST /trips/{id}/close`

Status transition завжди виконує domain guards, audit та транзакційну логіку.

## 2. Загальні headers

Для authenticated request:

- `Authorization` або secure cookie відповідно до auth mode;
- `X-Request-ID` — опційно від клієнта, інакше генерується сервером.

Для mutable aggregate:

- response: `ETag: "<row_version>"`;
- mutation: `If-Match: "<row_version>"`.

Для критичних повторюваних POST:

- `Idempotency-Key: <uuid-or-opaque-key>`.

## 3. Стандарт success response

Single object:

```json
{
  "data": {},
  "meta": { "request_id": "uuid" }
}
```

Collection:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 0,
    "request_id": "uuid"
  }
}
```

## 4. Стандарт error response

```json
{
  "error": {
    "code": "VEHICLE_TIME_CONFLICT",
    "message": "Локалізоване повідомлення для presentation layer",
    "details": {}
  },
  "meta": { "request_id": "uuid" }
}
```

`error.code` є стабільним machine-readable contract і не перекладається.

## 5. HTTP semantics

- `200` — успішна команда/читання;
- `201` — створено ресурс;
- `204` — успішна команда без body, де це доречно;
- `400` — malformed request;
- `401` — unauthenticated;
- `403` — permission denied;
- `404` — entity absent або недоступна tenant scope;
- `409` — resource/business/concurrency conflict;
- `422` — domain validation failure;
- `429` — rate limit;
- `500` — internal error з `request_id`.

## 6. Auth

- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/permissions`

Для browser deployment перевага надається HttpOnly Secure cookie/session strategy. Long-lived JWT у `localStorage` не є базовим рішенням.

## 7. Users / RBAC

- `GET /users`
- `POST /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `POST /users/{user_id}/activate`
- `POST /users/{user_id}/suspend`
- `POST /users/{user_id}/reset-password`
- `GET /users/{user_id}/roles`
- `PUT /users/{user_id}/roles`

## 8. Vehicles

Queries:

- `GET /vehicles`
- `GET /vehicles/{vehicle_id}`
- `GET /vehicles/{vehicle_id}/availability`
- `GET /vehicles/{vehicle_id}/history`
- `GET /vehicles/{vehicle_id}/documents`
- `GET /vehicles/{vehicle_id}/odometer`
- `GET /vehicles/{vehicle_id}/defects`
- `GET /vehicles/{vehicle_id}/maintenance`

Commands/data mutation:

- `POST /vehicles`
- `PATCH /vehicles/{vehicle_id}`
- `POST /vehicles/{vehicle_id}/activate`
- `POST /vehicles/{vehicle_id}/suspend`
- `POST /vehicles/{vehicle_id}/decommission`
- `POST /vehicles/{vehicle_id}/documents`
- `POST /vehicles/{vehicle_id}/documents/{document_id}/revoke`
- `POST /vehicles/{vehicle_id}/odometer-readings`

Фізичний DELETE production vehicle не є частиною API.

## 9. Drivers

- `GET /drivers`
- `POST /drivers`
- `GET /drivers/{driver_id}`
- `PATCH /drivers/{driver_id}`
- `GET /drivers/{driver_id}/availability`
- `GET /drivers/{driver_id}/history`
- `GET /drivers/{driver_id}/documents`
- `GET /drivers/{driver_id}/assignments`
- `POST /drivers/{driver_id}/activate`
- `POST /drivers/{driver_id}/suspend`
- `POST /drivers/{driver_id}/terminate`
- `POST /drivers/{driver_id}/documents`
- `POST /drivers/{driver_id}/documents/{document_id}/revoke`

## 10. Stops / Routes

- `GET /stops`
- `POST /stops`
- `GET /stops/{id}`
- `PATCH /stops/{id}`
- `POST /stops/{id}/activate`
- `POST /stops/{id}/deactivate`

- `GET /routes`
- `POST /routes`
- `GET /routes/{route_id}`
- `PATCH /routes/{route_id}`
- `GET /routes/{route_id}/versions`
- `POST /routes/{route_id}/versions`
- `GET /route-versions/{version_id}`
- `GET /route-versions/{version_id}/stops`
- `POST /route-versions/{version_id}/activate`
- `POST /route-versions/{version_id}/retire`

Historical used versions не редагуються in-place.

## 11. Schedules

- `GET /schedules`
- `POST /schedules`
- `GET /schedules/{id}`
- `GET /schedules/{id}/versions`
- `POST /schedules/{id}/versions`
- `GET /schedule-versions/{id}`
- `GET /schedule-versions/{id}/runs`
- `POST /schedule-versions/{id}/activate`
- `POST /schedule-versions/{id}/retire`
- `POST /schedule-versions/{id}/generate-trips`

`generate-trips` є ідемпотентною операцією для того самого `schedule_run_id + service_date`.

## 12. Trips

Queries:

- `GET /trips`
- `GET /trips/{trip_id}`
- `GET /trips/{trip_id}/timeline`
- `GET /trips/{trip_id}/planned-stops`
- `GET /trips/{trip_id}/actual-stops`
- `GET /trips/{trip_id}/events`

Commands:

- `POST /trips`
- `POST /trips/{id}/plan`
- `POST /trips/{id}/cancel`
- `POST /trips/{id}/depart`
- `POST /trips/{id}/complete`
- `POST /trips/{id}/close`
- `POST /trips/{id}/events`

Critical `close` використовує `If-Match` і `Idempotency-Key`.

## 13. Duties / Dispatch

- `GET /duties`
- `POST /duties`
- `GET /duties/{duty_id}`
- `GET /duties/{duty_id}/timeline`
- `GET /duties/{duty_id}/trips`
- `GET /duties/{duty_id}/assignments`
- `POST /duties/{duty_id}/add-trip`
- `POST /duties/{duty_id}/remove-trip`
- `POST /duties/{duty_id}/assign-vehicle`
- `POST /duties/{duty_id}/unassign-vehicle`
- `POST /duties/{duty_id}/assign-driver`
- `POST /duties/{duty_id}/unassign-driver`
- `POST /duties/{duty_id}/replace-vehicle`
- `POST /duties/{duty_id}/replace-driver`
- `POST /duties/{duty_id}/depart`
- `POST /duties/{duty_id}/return`
- `POST /duties/{duty_id}/close`
- `POST /duties/{duty_id}/cancel`

Resource conflict повертає `409` із конкретним conflict code/details.

## 14. Release

- `GET /releases`
- `GET /releases/{release_id}`
- `GET /duties/{duty_id}/release`
- `POST /duties/{duty_id}/release/open`
- `POST /releases/{id}/evaluate`
- `POST /releases/{id}/authorize`

`authorize`:

- `If-Match` required;
- `Idempotency-Key` required;
- fresh compliance evaluation всередині transaction;
- не довіряє попередньому UI/evaluation result.

## 15. Medical checks

- `GET /releases/{release_id}/medical-checks`
- `POST /releases/{release_id}/medical-checks`
- `GET /medical-checks/{check_id}`
- `POST /medical-checks/{check_id}/invalidate`

Completed check не PATCH-иться.

## 16. Technical checks

- `GET /releases/{release_id}/technical-checks`
- `POST /releases/{release_id}/technical-checks`
- `GET /technical-checks/{check_id}`
- `POST /technical-checks/{check_id}/invalidate`

Blocking checklist failure не може бути перетворений frontend-ом у `PASSED`.

## 17. Waybills

- `GET /waybills`
- `GET /waybills/{id}`
- `GET /waybills/{id}/versions`
- `GET /waybills/{id}/pdf`
- `POST /duties/{duty_id}/waybills`
- `POST /waybills/{id}/generate`
- `POST /waybills/{id}/issue`
- `POST /waybills/{id}/return`
- `POST /waybills/{id}/close`
- `POST /waybills/{id}/corrections`

`/reopen` для CLOSED Waybill не існує.

## 18. Fuel

- `GET /fuel-operations`
- `POST /fuel-operations`
- `GET /vehicles/{id}/fuel-summary`

Історична помилка виправляється reversal/correction, а не silent UPDATE.

## 19. Maintenance / Repairs

- `GET /defects`
- `POST /defects`
- `GET /maintenance`
- `POST /maintenance`
- `GET /repair-orders`
- `POST /repair-orders`
- `POST /repair-orders/{id}/diagnose`
- `POST /repair-orders/{id}/approve`
- `POST /repair-orders/{id}/start`
- `POST /repair-orders/{id}/wait-parts`
- `POST /repair-orders/{id}/complete`
- `POST /repair-orders/{id}/verify`
- `POST /repair-orders/{id}/close`

## 20. Reports

- `GET /reports/daily-trips`
- `GET /reports/trips`
- `GET /reports/vehicle-work`
- `GET /reports/driver-work`
- `GET /reports/mileage`
- `GET /reports/cancellations`
- `GET /reports/releases`
- `GET /reports/fuel-consumption`
- `GET /reports/expiring-documents`
- `GET /reports/maintenance`

Для важких export:

- `POST /report-exports`
- `GET /report-exports/{id}`
- `GET /report-exports/{id}/file`

## 21. Audit

- `GET /audit`
- `GET /audit/entities/{entity_type}/{entity_id}`

Немає `PATCH` або `DELETE` audit endpoint.

## 22. Pagination/filtering

Collection endpoints підтримують стандартні query params:

- `page`;
- `page_size`;
- `sort` — whitelist;
- domain-specific filters.

`page_size` має server max.

## 23. Date/time contract

- instants: ISO-8601 з offset, backend canonical storage — `timestamptz`;
- business `service_date`: `YYYY-MM-DD`;
- time-of-day schedule values: local time semantics + version context;
- default business timezone deployment: `Europe/Kyiv`, але timezone є company setting.

## 24. Locale contract

- `Accept-Language` може керувати presentation messages;
- business codes/status values не локалізуються;
- API data не дублюється під кожну locale;
- default locale — `uk`.

## 25. API freeze rule

Після M0 incompatible зміна endpoint/request/response/error semantics вимагає:

1. GitHub Issue;
2. impact analysis;
3. оновлення цього контракту;
4. OpenAPI schema update;
5. contract tests;
6. versioning/deprecation decision, якщо compatibility порушується.