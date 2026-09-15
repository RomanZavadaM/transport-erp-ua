# Ролі та робочі простори

Статус: **M0 UX freeze draft**

Ролі визначають початковий workspace і типові сценарії, але backend authorization базується на permissions. Один користувач може мати кілька ролей; UI об'єднує дозволені можливості без створення “super-user screen”.

## 1. Керівник

### Landing

`Dashboard керівника`

### Основні блоки

- operational KPI за день;
- заплановано / випущено / on line / returned / cancelled;
- блокування випуску;
- vehicle availability / repair;
- document expiry;
- mileage / fuel summary;
- links до management reports;
- audit/search read-only.

### Flow

`Dashboard → drill-down filtered list → entity card → history/audit`.

Керівник не редагує operational history лише тому, що має management role.

## 2. Диспетчер

### Landing

`Dispatcher Board`.

### Основний flow дня

```text
Рейси дня
→ створити/перевірити Duty
→ призначити vehicle/driver
→ відслідкувати checks
→ Release Workspace
→ Waybill
→ authorize
→ depart
→ monitor Trip execution
→ return
→ close Trips
→ close Duty/Waybill
```

### UX-принцип

Диспетчер не повинен повертатися в `Автобуси` або `Водії`, щоб виконати звичайне призначення. Master-data screens — для довідникової роботи; operational assignment виконується в Duty/Board.

## 3. Механік

### Landing

`Технічний контроль — черга`.

```text
Очікують: 7     Failed/needs action: 2

05:40  ВС1234АА  Duty D-001  [Відкрити]
05:45  ВС7777АА  Duty D-003  [Відкрити]
...
```

### Check flow

`Queue → Check Workspace → identify vehicle/Duty → odometer → checklist → defects → confirm result`.

Check Workspace:

- vehicle identity завжди visible;
- current Duty/driver summary;
- latest odometer;
- checklist sections;
- defect entry inline;
- submit summary.

Після completion форма стає read-only. Для помилки — окрема `Визнати недійсним` action із reason.

### Maintenance flow

`Vehicle/Defect → Repair Order → state transitions → verification → close`.

Technical check і repair UI мають спільний vehicle context, але це різні workflows.

## 4. Медик

### Landing

`Медичний контроль — черга`.

Показується мінімум:

- ПІБ водія;
- ідентифікатор/табельний номер;
- Duty;
- planned departure;
- status check.

### Flow

`Queue → Driver check → Result → Confirm`.

UI не показує fuel, financial, repair чи інші непотрібні дані.

Після completion check immutable; correction через invalidation.

Медичний UX не повинен провокувати внесення зайвих медичних даних, якщо transport workflow потребує лише decision result.

## 5. Водій

### Landing

`Мій робочий день`.

MVP мінімум:

- current/next Duty;
- vehicle;
- route/trips;
- planned times;
- own Waybill access, якщо дозволено;
- own history;
- `Повідомити про несправність/подію`, якщо feature enabled.

На desktop web роль може бути read-mostly. Native mobile app — post-MVP.

Driver scope завжди `own`; direct URL іншого driver/entity не обходить backend permission.

## 6. Адміністратор

### Landing

`Адміністрування`.

Секції:

- Users;
- Roles;
- Permissions matrix;
- Company/Depot settings;
- Document templates;
- Check templates;
- Numbering;
- Locales;
- reference dictionaries.

Admin не бачить кнопки `Авторизувати випуск` лише через admin role.

## 7. System worker

Не має UI workspace як людина.

Admin/operations може бачити лише monitoring projection:

- queued/failed jobs;
- report exports;
- outbox health;
- integrity alerts.

## 8. Multi-role user

Якщо користувач має, наприклад, dispatcher + manager permissions:

- sidebar містить обидві дозволені секції;
- default landing configurable/preference;
- actions усе одно перевіряються permission-by-permission.

Не створювати комбіновані “role-specific copies” однієї entity page.

## 9. Sidebar/navigation visibility

Секція меню видима, якщо користувач має хоча б один meaningful permission для неї.

Приклад:

- `Паливо` не показується медику;
- `Користувачі` не показуються водію;
- `Медконтроль` не показується механіку без відповідного permission;
- `Аудит` може бути read-only для керівника.

## 10. Cross-role handoff

System не вимагає усного “я вже зробив”.

Статус змінюється server-side і стає visible наступній ролі:

- dispatcher створив Release Pending → mechanic/medic queue;
- medic completed → Dispatcher Board оновився;
- mechanic failed + defect → dispatcher бачить BLOCKED;
- resource replaced → new required check з'являється у відповідній queue.

SSE/notifications прискорюють handoff, але backend state є source of truth.

## 11. Notifications

MVP notification center може показувати operational alerts:

- required check waiting;
- blocking defect;
- resource assignment removed/replaced;
- Waybill generation failed;
- concurrency change affecting open workspace.

Не перетворюємо notifications на дубль email/chat system.

## 12. Locale

Default UI locale — `uk`.

Supported:

- `uk`;
- `en`;
- `es`;
- `fr`;
- `de`.

Перемикання locale:

- не змінює domain codes/data;
- не скидає current workspace/filter;
- не створює іншу business logic;
- не змінює юридично сформований historical PDF автоматично.

## 13. Session / workstation behavior

На shared office workstation:

- user identity завжди видима;
- logout легко доступний;
- sensitive action не виконується після expired session;
- після relogin не відновлюється незахищений sensitive form іншого користувача.

## 14. Role UX acceptance

Кожна роль повинна:

- потрапляти після login у meaningful workspace;
- виконувати свій primary daily flow без навігації через непотрібні модулі;
- бачити лише дозволені дані/actions;
- отримувати зрозумілий handoff від попередньої ролі;
- не мати generic state override;
- не потребувати admin role для нормальної operational роботи.