# Локалізація системи

Статус: **M0 i18n contract**

## Канонічна locale

`uk` — default і canonical locale TransportERP-UA.

Підтримувані locale системи:

- `uk`;
- `en`;
- `es`;
- `fr`;
- `de`.

## Архітектурний принцип

Мова не створює окремої бізнес-логіки.

Однаковими для всіх locale залишаються:

- state machines;
- permissions;
- validation/business rules;
- API paths/codes;
- DB status values;
- event names;
- entity identifiers.

## Детальний контракт

- [Locale Resource Contract](i18n/Locale-Resource-Contract.md) — locale resolution, UI resources, formatting, stable API/DB codes;
- [Document Locale Contract](i18n/Document-Locale-Contract.md) — document/PDF locale, template versions, historical immutability;
- [Translation Governance](i18n/Translation-Governance.md) — source-of-truth, statuses, glossary, review;
- [Localization Testing Matrix](i18n/Localization-Testing.md) — UI/API/PDF test coverage.

## Frontend

Інтерфейс використовує stable translation keys. Components не зберігають окремі hardcoded тексти для кожної мови.

## API

Backend повертає stable machine-readable codes. Locale не змінює `error.code`, permission або state value.

## Database

Technical values не перекладаються. Реальні назви маршруту, зупинки, підприємства тощо є domain data, а не UI resources.

## PDF / документи

`document_template_versions` мають explicit locale/version. Зміна user locale не змінює вже створений historical PDF або snapshot.

## Форматування

Presentation layer локалізує дати, час, числа, валюту, pluralization і labels. PostgreSQL/API зберігають typed neutral values.
