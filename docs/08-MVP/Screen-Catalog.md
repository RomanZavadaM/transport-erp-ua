# Каталог екранів MVP

Статус: **M0 draft**

Мета документа — зафіксувати мінімальний набір робочих екранів. Це не pixel-perfect дизайн; це функціональна карта frontend.

## 1. Загальні правила UI

- українська locale за замовчуванням;
- підтримка `uk/en/es/fr/de` через locale resources;
- статуси не керуються універсальним dropdown;
- критичні переходи виконуються явними action buttons;
- причини блокування показуються текстом, а не лише кольором;
- closed history за замовчуванням read-only;
- конкурентна зміна показується як conflict, а не silent overwrite;
- списки мають серверні filters/sort/pagination;
- ключові operational екрани оптимізовані для desktop, але залишаються responsive.

## 2. Dashboard

### Керівник

Показники дня:

- заплановано рейсів;
- випущено;
- на лінії;
- завершено;
- скасовано;
- заблоковано до випуску;
- автобуси active / repair / blocked;
- документи з критичним expiry;
- базові fuel/mileage indicators.

Drill-down веде до відповідного filtered list.

### Диспетчер

Operational summary + direct link до Dispatcher Board.

## 3. Автобуси

### Vehicle List

Колонки:

- гаражний номер;
- реєстраційний номер;
- марка/модель;
- depot;
- lifecycle state;
- calculated availability;
- current odometer;
- blocking issue indicator.

### Vehicle Card

Вкладки/секції:

- основні дані;
- документи;
- одометр/history;
- assignments/usage;
- defects;
- ТО;
- ремонти;
- audit/history.

## 4. Водії

### Driver List

- табельний номер;
- ПІБ;
- depot;
- employment state;
- calculated availability;
- expiry indicator.

### Driver Card

- основні дані;
- документи;
- категорії/допуски;
- assignments;
- trips/duties;
- audit/history.

Чутливі дані проєктуються відповідно до permission projection.

## 5. Маршрути та зупинки

### Stops List / Stop Card

CRUD лише для master data, з archive/deactivate замість destructive delete після використання.

### Routes List

- номер;
- назва;
- type;
- current version;
- status.

### Route Version Editor

- validity period;
- direction;
- ordered stops;
- distances;
- planned timing;
- activate/retire commands.

Використана historical version не редагується in-place.

## 6. Розклад

### Schedule List

- маршрут;
- version;
- validity;
- status.

### Schedule Editor

- service calendar;
- runs;
- departure/arrival;
- stop times;
- exceptions.

### Generate Trips Dialog

- date range;
- preview counts;
- idempotent generation result;
- conflict/error summary.

## 7. Trips

### Trip List

Фільтри:

- service date/period;
- route;
- status;
- Duty;
- vehicle;
- driver.

### Trip Card

- planned data;
- Duty membership;
- actual data;
- stop plan/actuals;
- event timeline;
- close/cancel commands according to state.

## 8. Dispatcher Board — головний operational screen

Режим дня / depot.

Основні колонки:

- плановий час;
- маршрут/рейс;
- Duty;
- автобус;
- водій;
- документи;
- медичний контроль;
- технічний контроль;
- Release;
- Waybill;
- план/факт;
- відхилення.

Обов’язкові можливості:

- quick filters: проблемні / неукомплектовані / готові / on line / returned;
- assign/replace resource;
- відкрити Release Workspace;
- відкрити Waybill;
- бачити live server notifications через SSE або equivalent;
- conflict message при stale data;
- no hidden critical actions.

## 9. Duty Workspace

Сторінка одного наряду:

- service date і time range;
- список Trips;
- planned vehicle assignments;
- planned driver assignments;
- actual usage periods;
- Release state;
- Waybill;
- events/timeline;
- depart/return/close commands.

## 10. Release Workspace

Один екран повного decision context.

Блоки:

- Duty/Trips;
- assigned vehicle;
- assigned drivers;
- vehicle documents;
- driver documents;
- medical check;
- technical check;
- defects/repairs;
- compliance rule evaluations;
- Waybill readiness;
- authorization action.

Кнопка `Авторизувати випуск` disabled при known blocking FAIL і завжди повторно перевіряється backend при натисканні.

## 11. Medical Queue / Check

Медик бачить:

- чергу required checks;
- мінімальні дані водія;
- Duty;
- форму результату;
- history власних checks за permission.

Немає доступу до непотрібних operational/financial даних.

## 12. Technical Queue / Check

Механік бачить:

- чергу автобусів;
- vehicle identification;
- current/last odometer;
- checklist;
- defect entry;
- result.

## 13. Waybills

### Waybill List

- номер;
- дата;
- Duty;
- vehicle;
- driver(s);
- status;
- current version;
- PDF available.

### Waybill Card

- business data;
- version history;
- PDF preview/download/print;
- issued/returned/closed timestamps;
- correction cases;
- audit timeline.

Після close — жодної кнопки generic edit.

## 14. Рух / фактичне виконання

Operational list:

- on-line Duties;
- active Trips;
- delay/breakdown indicators;
- departed/returned timestamps;
- missing actual facts.

До GPS-модуля це подієвий/табличний екран, не live map.

## 15. Паливо

### Fuel Operations

- vehicle;
- date/time;
- operation type;
- liters;
- odometer;
- Duty/Waybill refs;
- source;
- correction/reversal link.

### Fuel Summary

- vehicle;
- period;
- quantity;
- mileage;
- calculated l/100 km.

## 16. ТО та ремонти

### Defects

- active/blocking;
- vehicle;
- source;
- severity;
- resolution status.

### Maintenance

- planned due date/km;
- completed events.

### Repair Orders

- number;
- vehicle;
- status;
- blocks operation;
- dates;
- cost summary.

## 17. Документи

Cross-entity expiry dashboard:

- owner type;
- owner;
- document type;
- number;
- valid until;
- blocking policy;
- state.

Quick filters: expired, <=7, <=30, <=60 days.

## 18. Звіти

Report catalog + parameter form + table result + permitted export.

MVP reports визначені в `MVP-Definition-Package.md`.

## 19. Користувачі / ролі

- Users List/Card;
- enable/disable;
- Roles;
- Permissions Matrix;
- sessions/security overview в межах MVP.

## 20. Audit

### Entity Timeline

Людинозрозуміле представлення:

- коли;
- хто;
- дія;
- причина;
- before/after для дозволених полів.

### Audit Search

Для authorized ролей:

- date range;
- actor;
- entity type/id;
- action;
- request/correlation id.

Raw JSON не є основним UX.

## 21. Налаштування

MVP settings:

- company/depot;
- timezone;
- default locale;
- document/check templates;
- numbering rules;
- document warning thresholds;
- feature/policy settings, які затверджені M0.

## 22. Екрани, яких у MVP не буде

- GPS live map;
- ticket sales terminal;
- passenger analytics;
- payroll;
- бухгалтерський ledger;
- spare-parts warehouse full UI;
- external partner portal;
- native mobile driver application.

Їх відсутність є контрольованим scope decision, а не “недоробкою MVP”.