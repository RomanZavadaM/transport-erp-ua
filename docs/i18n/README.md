# Мовна політика документації

## Канонічна мова

**Українська (`uk`) є основною та канонічною мовою TransportERP-UA.**

Усі архітектурні рішення, бізнес-правила, state machines, acceptance criteria, API-контракти та затверджені інтерпретації вимог спочатку фіксуються українською.

## Підтримувані переклади

- English — `en`
- Español — `es`
- Français — `fr`
- Deutsch — `de`

Переклади зберігаються у `docs/i18n/<lang>/`.

## Пріоритет

Якщо переклад суперечить українському оригіналу, чинним є український source.

Переклад не створює нової бізнес-вимоги й не змінює semantic meaning canonical документа.

## Application i18n contract

Детальна системна політика:

- [`Locale-Resource-Contract.md`](../01-Architecture/i18n/Locale-Resource-Contract.md) — UI resources, locale resolution, formatting, stable API/DB codes;
- [`Document-Locale-Contract.md`](../01-Architecture/i18n/Document-Locale-Contract.md) — PDF/document templates, locale/version, historical immutability;
- [`Translation-Governance.md`](../01-Architecture/i18n/Translation-Governance.md) — source-of-truth, review/status, glossary, stable identifiers;
- [`Localization-Testing.md`](../01-Architecture/i18n/Localization-Testing.md) — locale/layout/API/PDF test matrix.

## Статуси перекладів

- `current`;
- `needs-review`;
- `outdated`.

## Metadata перекладу

Переклад повинен вказувати:

- canonical source path;
- source commit/version;
- translation status.

## Stable technical identifiers

Не перекладаються:

- API paths;
- JSON field names;
- error codes;
- permissions;
- DB names;
- state values;
- event names;
- translation keys;
- `BR-*`, `AT-*`, ADR IDs.

## Architecture Freeze

M0 freeze перевіряє українську canonical документацію та сам i18n contract.

Похідні переклади можуть оновлюватися після freeze без зміни архітектури, якщо не змінюють canonical meaning.
