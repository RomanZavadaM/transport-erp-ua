# Спільні UX-патерни TransportERP-UA

Статус: **M0 UX freeze draft**

Цей документ забороняє різним модулям реалізовувати однакові ситуації по-різному.

## 1. Status ≠ dropdown

Business state machine не редагується полем:

`Status: [CLOSED ▼]`.

Замість цього показуються лише дозволені commands:

- `Призначити автобус`;
- `Авторизувати випуск`;
- `Зафіксувати повернення`;
- `Закрити`;
- `Скасувати`.

Backend є джерелом allowed transition.

## 2. Critical action hierarchy

- Primary action — одна основна next-step command на workspace;
- Secondary — safe supporting actions;
- Destructive/terminal — visually distinct і з confirmation;
- forbidden action не маскується generic admin override.

## 3. Blocked state

Заборонено показувати лише:

`Операція неможлива`.

Потрібно:

- конкретний code/reason;
- subject;
- що треба виправити;
- link/action, якщо доступно;
- чи warning є blocking.

При кількох причинах показати всі blocking reasons або count + expand.

## 4. Validation

### Field validation

Показувати біля поля, коли це input-level проблема:

- неправильний формат;
- required field;
- invalid time range.

### Domain validation

Показувати form-level/problem panel:

- Duty має open Trips;
- Release not ready;
- resource conflict;
- closed history immutable.

Не підсвічувати випадкове поле для domain error.

## 5. 409 Conflict

### Concurrent modification

Поведінка:

1. зупинити save/command;
2. не overwrite;
3. показати current change warning;
4. запропонувати refetch/compare;
5. користувач повторно ухвалює рішення на нових даних.

### Resource conflict

Показати:

- resource;
- conflict period;
- conflicting Duty/Trip, якщо permission дозволяє;
- candidates/next action.

## 6. Idempotent retry

Під час pending command:

- button disabled/loading;
- UI зберігає Idempotency-Key для logical attempt;
- network timeout не означає автоматично failure;
- спочатку retry same key/refetch current state.

Не генерувати новий Idempotency-Key на кожний автоматичний retry тієї самої дії.

## 7. Confirmations

Confirmation потрібен для:

- cancel Trip/Duty;
- authorize Release;
- issue/close Waybill;
- close Duty/Trip;
- invalidate completed check;
- resource replacement після start/authorization;
- correction submission/approval;
- revoke document;
- deactivate/decommission/terminate significant master entity.

Confirmation не потрібен для звичайного search/filter/navigation.

## 8. Reason required

Коли business audit потребує reason, modal/form не дозволяє submit без нього.

Reason code — structured select; comment — окреме поле.

Не зберігати всю семантику лише в free text.

## 9. Tables and overflow

Operational tables:

- sticky header;
- meaningful sticky first columns;
- explicit horizontal scrollbar/overflow affordance;
- actions reachable без зміни browser zoom;
- column width не стискається до нечитабельного стану;
- user can select/copy text.

Dropdown/menu не повинні обрізатися overflow контейнером; overlays рендеряться у відповідному portal/layer.

## 10. Scrolling forms

Довга форма:

- page scroll preferred;
- nested scroll лише для clearly bounded panel/list;
- primary action може бути sticky footer, якщо form довга;
- footer не перекриває останні поля;
- scrollbar visible/usable.

Не створювати три nested scroll containers без необхідності.

## 11. Modal vs Drawer vs Page

### Modal

Коротке рішення:

- confirmation;
- reason;
- small assignment selector;
- single compact action.

### Drawer

Contextual details без втрати list position:

- Duty summary;
- history preview;
- candidate info.

### Full page/workspace

Складний multi-section workflow:

- Release;
- Waybill;
- Route/Schedule editor;
- Vehicle/Driver card;
- Repair Order.

## 12. Form drafts

Для довгих editable draft entities browser accidental navigation може викликати unsaved-changes prompt.

Critical business commands не “автозберігаються” silently.

Master-data edit може мати explicit Save.

## 13. Date/time inputs

- date picker + keyboard input;
- display locale-aware;
- underlying API ISO contract;
- planned vs actual labels завжди explicit;
- overnight times показують date/day offset, щоб уникнути двозначності.

Не використовувати лише номер місяця в human-facing report/header там, де потрібна читабельність.

## 14. Search/selectors

Vehicle/driver/route selectors:

- searchable by obvious identifiers;
- keyboard navigable;
- show disambiguating secondary fields;
- server-side search for large datasets;
- recent/selected item visible;
- clear selection explicit.

Не використовувати dropdown із сотнями options без search.

## 15. Copy/paste

Standard text copy працює всюди, де security policy не забороняє.

Editable text inputs підтримують browser/OS copy-paste.

Табличні значення можна виділяти/copy.

Не перехоплювати Ctrl/Cmd+C/V глобально без необхідності.

## 16. Loading

### Query

Skeleton/placeholder, але layout стабільний.

### Command

Specific action shows progress.

Якщо operation async (PDF/report):

- command завершується створенням job/artifact state;
- UI показує pending status;
- користувач не блокується full-page spinner-ом довгий час.

## 17. Errors

Unexpected server error:

```text
Не вдалося виконати операцію.
Request ID: 123e...
[Повторити] [Скопіювати ID]
```

Не показувати raw SQL/stack trace.

## 18. Success feedback

Не показувати toast `Успішно` після кожного GET/filter.

Command success:

- row/state visibly changes;
- toast потрібен лише якщо change неочевидна або user залишив workspace.

## 19. Notifications vs errors

Toast не використовується як єдине місце для critical blocking error: він зникає.

Blocking/domain error залишається в relevant workspace/problem panel, доки причина актуальна.

## 20. Closed/history visual mode

Closed entity має явний read-only banner:

`Закрито 15.09.2026 18:42 • Іваненко Д.`

Actions:

- history;
- print/export;
- correction workflow, якщо permission.

Немає “Edit” поруч із historical facts.

## 21. Accessibility baseline

- keyboard access;
- visible focus;
- semantic labels;
- errors associated with fields;
- no color-only meaning;
- adequate contrast;
- minimum target size for frequent actions;
- screen-reader friendly live status for async completion.

## 22. Localization resilience

Layout тестується не лише українською.

German/French labels можуть бути довшими, тому:

- кнопки не мають fixed tiny width;
- text may wrap where appropriate;
- status codes not displayed raw as primary label;
- table columns can adapt/tooltip.

## 23. Permission changes during session

Якщо permission відкликано під час відкритої сторінки:

- backend поверне 403;
- frontend refresh effective permissions;
- action прибирається/disabled;
- already loaded sensitive details очищаються/refetched if scope changed.

## 24. Dangerous bulk actions

Bulk operations для critical business state в MVP мінімізуються.

Якщо з'явиться bulk command:

- preview affected entities;
- per-item validation;
- explicit confirmation;
- partial failure semantics documented;
- audit per entity/batch.

Особливо не створювати небезпечну кнопку на кшталт “заповнити/закрити все” без окремого architecture/business review.