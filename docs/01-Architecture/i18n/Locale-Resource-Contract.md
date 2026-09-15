# Locale Resource Contract

Статус: **M0 i18n contract**

## Підтримувані locale

- `uk` — default і canonical;
- `en`;
- `es`;
- `fr`;
- `de`.

## Locale resolution

Порядок:

1. explicit user preference;
2. company/user default, якщо визначений;
3. browser preference, якщо підтримується;
4. fallback `uk`.

Unsupported locale завжди fallback у `uk`.

## Frontend resources

UI використовує stable semantic keys:

```text
nav.dashboard
release.status.blocked
release.action.authorize
waybill.action.issue
trip.error.vehicle_conflict
common.action.cancel
```

Компоненти не містять п'ять копій тексту.

Recommended namespaces:

- `common`;
- `navigation`;
- `auth`;
- `fleet`;
- `drivers`;
- `routes`;
- `schedules`;
- `trips`;
- `duties`;
- `release`;
- `waybills`;
- `fuel`;
- `maintenance`;
- `reports`;
- `audit`;
- `admin`;
- `errors`.

## Key naming

Key описує semantic meaning, а не конкретний текст.

Добре:

```text
release.block_reason.expired_vehicle_document
```

Погано:

```text
red_text_4
message_left_column
```

## API contract

Backend повертає stable codes:

```text
VEHICLE_TIME_CONFLICT
DRIVER_TIME_CONFLICT
RELEASE_NOT_READY
CONCURRENT_MODIFICATION
```

`error.code` і domain status values не перекладаються залежно від locale.

Frontend не аналізує текст message для business logic.

## Database values

Technical values залишаються стабільними:

```text
CLOSED
AUTHORIZED
BLOCKED
PASSED
FAILED
```

У БД не створюються різні status values для різних мов.

## Business data

Назва підприємства, маршруту, зупинки, документа та інші фактичні значення — domain data, а не UI resource.

Якщо пізніше потрібні multilingual public names, вони додаються окремими translation tables без зміни identity сутності.

## Formatting

Locale presentation layer відповідає за:

- date/time display;
- decimal/grouping display;
- currency display;
- percentage display;
- pluralization;
- translated unit labels.

API і PostgreSQL зберігають typed neutral values.

## Time

Storage використовує `timestamptz` та `date` згідно з data contract.

Для operational timestamps у UI уникаємо двозначних month/day formats.

Український baseline:

```text
15.09.2026 08:45
```

## Units MVP

- distance — km;
- fuel — l;
- fuel efficiency — l/100 km.

Перекладається label, але не domain meaning.

## Pluralization

Resource engine повинен підтримувати plural rules конкретної locale.

Не можна формувати всі мови просто як `count + singular/plural`.

## Locale switch

Зміна UI locale:

- не змінює business state;
- не regenerates historical documents;
- може зберігатися як user preference;
- не створює нової business version сутності.

## Missing key fallback

Fallback chain:

```text
selected locale → uk → diagnostic marker/log
```

Missing translation не повинна блокувати domain command.

## Layout tolerance

UI тестується не тільки на короткому українському/англійському тексті.

Особливо перевіряються довші німецькі та французькі labels у:

- Dispatcher Board;
- Release Workspace;
- buttons/toolbars;
- dialogs;
- tables;
- navigation.

Критична action не може зникнути через довший переклад.
