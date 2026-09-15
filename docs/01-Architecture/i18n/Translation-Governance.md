# Translation Governance

Статус: **M0 i18n contract**

## Source of truth

Українська версія є canonical source. Переклади `en/es/fr/de` є похідними та не створюють окремих вимог.

## Статуси

- `current` — синхронізовано з canonical source;
- `needs-review` — переклад потребує перевірки;
- `outdated` — український source змінився після перекладу.

## Metadata

Для перекладеного документа фіксуються:

- canonical source path;
- source commit/version;
- translation status;
- optional reviewer/date.

## Порядок зміни

1. змінюється український canonical source;
2. проходить review змісту;
3. affected translations позначаються для оновлення;
4. переклади синхронізуються;
5. переклад не змінює canonical meaning.

## Stable identifiers

Однаковими в усіх мовах залишаються:

- `BR-*`;
- `AT-*`;
- ADR IDs;
- API error codes;
- permission codes;
- event names;
- technical state values;
- translation keys.

Не створюються окремі мовні IDs для одного правила.

## Domain glossary

Ведеться multilingual glossary для термінів:

- Trip;
- Duty;
- Release;
- Waybill;
- Vehicle;
- Driver;
- Dispatch;
- Checks;
- основних states/actions.

Переклад не повинен змінювати domain meaning терміна.

## Не перекладаються

- API paths;
- JSON field names;
- DB table/column names;
- error/permission codes;
- state values;
- translation keys;
- event types.

## Review

Перевіряються:

- точність терміна;
- зрозумілість action/status;
- довжина UI label;
- placeholders;
- accessibility labels;
- consistent terminology.

## Placeholder compatibility

Placeholder names стабільні.

Canonical:

```text
waybill.number = "Шляховий лист №{number}"
```

У перекладі `{number}` зберігається без перейменування.

## Completeness

Для supported locale validation повинна виявляти:

- missing required keys;
- obsolete keys;
- placeholder mismatch;
- invalid resource syntax.

## Production support

`uk` має бути complete/current для production release.

Інша locale вважається production-supported лише коли її critical navigation, actions, statuses та error messages достатньо повні. Інакше працює fallback на `uk`.

## Git workflow

Значне оновлення перекладу проходить PR із зазначенням:

- locale;
- canonical source version;
- translation status;
- affected terminology/resources.

Якщо пропонована зміна змінює зміст бізнес-поняття, спочатку змінюється canonical українська специфікація, а не лише переклад.
