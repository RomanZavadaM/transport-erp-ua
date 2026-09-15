# Waybill Workspace

Статус: **M0 UX freeze draft**

Waybill Workspace керує життєвим циклом шляхового листа, але не перетворюється на універсальний PDF-редактор. Бізнес-дані змінюються через відповідні domain workflows; PDF є versioned representation цих даних.

## 1. Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ← Duty D-001     Шляховий лист № 2026/000123     ISSUED        Version 2                 │
├────────────────────────────────────────┬─────────────────────────────────────────────────┤
│ ДАНІ                                   │ PDF                                             │
│ Підприємство: ...                      │ ┌─────────────────────────────────────────────┐ │
│ Автобус: ВС1234АА                      │ │                                             │ │
│ Водій: Іваненко І.І.                   │ │              PDF preview                    │ │
│ Duty: D-001                            │ │                                             │ │
│ Trips: 101, 104, 109                   │ └─────────────────────────────────────────────┘ │
│ Виїзд: 05:58                           │ [Відкрити PDF] [Друк] [Завантажити]           │
│ Повернення: —                          │                                                 │
├────────────────────────────────────────┴─────────────────────────────────────────────────┤
│ Versions: v1 GENERATED 05:52 • v2 ISSUED 05:55                                           │
│ [Історія версій]                                            [Повернути] [Закрити]        │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Header

Постійно видимі:

- full business number;
- status;
- Duty;
- current version;
- issue/return/close timestamps;
- warning, якщо PDF generation pending/failed.

## 3. Data panel

Показує snapshot-relevant business data у human-readable form.

До issue:

- дозволені source data можуть бути змінені у відповідному domain screen;
- Waybill regenerate створює нову version за policy.

Після issue:

- номер незмінний;
- historical generated/issued versions залишаються;
- зміна business facts відбувається через operational facts / correction workflow, а не редагування PDF-полів.

## 4. PDF preview

Preview є окремим render artifact.

UI показує:

- generation state: `PENDING / READY / FAILED`;
- template code/version/locale;
- generated_at;
- PDF hash/details у technical view;
- actions print/open/download за permission.

Не треба автоматично regenerate PDF при кожному відкритті сторінки.

## 5. Generate flow

`Сформувати документ`:

1. показує summary source data/template;
2. викликає idempotent generate command;
3. створює business version/job;
4. показує `Формується…`;
5. worker result оновлюється через poll/SSE;
6. при FAILED показує retry, що не створює нову business version без command semantics.

## 6. Issue flow

Перед `Видати` confirmation:

```text
Видати шляховий лист №2026/000123?

Duty: D-001
Автобус: ВС1234АА
Водій: Іваненко І.І.
PDF: READY, version 2

Після видачі номер і видана версія залишаться в історії.

[Скасувати] [Видати]
```

## 7. Active / Returned / Closing

Workspace показує actual facts as they become available:

- departure time/odometer;
- return time/odometer;
- calculated mileage;
- fuel facts;
- included Trips and their completion states.

Missing required closing facts виділяються окремим checklist, а не загальним повідомленням.

## 8. Close flow

`Закрити` доступна лише за allowed state/permission.

Перед close UI показує:

```text
Готовність до закриття
✓ Duty RETURNED
✓ Усі обов'язкові Trips CLOSED/CANCELLED
✓ Показники одометра
✓ Фінальна версія документа
⚠ Fuel data — warning / required according to policy
```

Backend повторно перевіряє всі guards.

Після `CLOSED` сторінка read-only щодо historical business content.

## 9. Version history

Окремий drawer/table:

| Version | Стан | Template | Created | Actor | Reason |
|---|---|---|---|---|---|
| v1 | READY | UA v3 | 05:52 | dispatcher | initial |
| v2 | READY/ISSUED | UA v3 | 05:55 | dispatcher | regenerate before issue |
| v3 | correction | UA v3 | later | authorized user | correction case #... |

Клік відкриває historical PDF/snapshot саме цієї version.

## 10. Correction closed document

Після `CLOSED` немає кнопки `Редагувати` або `Відкрити знову`.

Action:

`Створити запит на виправлення`.

Форма:

- reason code;
- required explanation;
- fields/context to correct;
- optional supporting attachment.

Після approval correction workflow створює new version. Old version залишається доступною в history.

## 11. Print semantics

Print action друкує конкретну selected version.

UI чітко показує:

- `Поточна версія`;
- `Історична версія v1`;
- `Коригувальна версія`.

Не можна непомітно надрукувати regenerated сучасний template замість original historical PDF.

## 12. Template locale

Для українського deployment default legal document locale — `uk`, якщо regulatory/business policy не визначила інше.

Зміна UI locale користувача не перегенеровує historical document іншою мовою.

Template locale/version є властивістю Waybill version.

## 13. Failure handling

### PDF generation failed

Показати:

- error code / human message;
- version/job identity;
- retry action;
- support request ID.

Не видаляти Waybill або номер.

### Concurrent close/issue

`409 CONCURRENT_MODIFICATION` → refetch + current state. Якщо інший user already issued/closed, UI показує фактичний результат.

## 14. Audit integration

Timeline включає:

- created;
- number allocated;
- version generated;
- issued;
- PDF generation failure/retry;
- returned;
- closed;
- correction requested/approved/applied.

## 15. Acceptance criteria

- Waybill number завжди однозначно visible;
- historical version можна відкрити повторно;
- print працює для конкретної stored PDF version;
- regenerate не переписує попередній PDF;
- closed document не має generic edit/reopen;
- correction reason/history видима;
- missing close facts пояснені конкретно;
- UI locale не змінює historical document content.