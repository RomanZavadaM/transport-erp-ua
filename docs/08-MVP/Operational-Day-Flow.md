# Наскрізний робочий день підприємства

Статус: **M0 draft**  
Мета: зафіксувати production workflow, який перший MVP повинен пройти без ручних обхідних схем.

## 1. Підготовка напередодні / до початку зміни

Диспетчер відкриває operational day та бачить згенеровані за чинним розкладом рейси.

Система повинна:

- згенерувати відсутні регулярні рейси ідемпотентно;
- показати скасовані/додаткові рейси окремо;
- показати конфлікти даних або відсутні ресурси;
- не змінювати вже створені історичні рейси при редагуванні нового schedule version.

Диспетчер формує `Duty` — наряд, що може включати 1..N рейсів.

## 2. Призначення ресурсів

До Duty призначаються:

- автобус;
- primary driver;
- за потреби інші водії/ролі екіпажу.

При кожному призначенні backend повторно перевіряє доступність ресурсу, а PostgreSQL гарантує відсутність overlap.

UI-перевірка доступності є лише підказкою; джерело істини — транзакція і DB constraint.

Якщо ресурс уже зайнятий, команда завершується `409 Conflict` з machine-readable code і посиланням на конфліктний Duty.

## 3. Передрейсовий контроль

Duty переходить у `RELEASE_PENDING`.

### 3.1. Медичний контроль

Медик бачить лише необхідний мінімум даних водія і Duty.

Результат:

- `PASSED/FIT`;
- `FAILED/UNFIT`.

Completed check не редагується. Помилка виправляється через invalidation + new check.

### 3.2. Технічний контроль

Механік перевіряє фактично призначений автобус.

Фіксуються:

- odometer;
- checklist results;
- result;
- defects.

Blocking defect автоматично впливає на release evaluation.

## 4. Compliance evaluation

Система оцінює правила випуску на момент перевірки.

Мінімально:

- active vehicle assignment;
- active required driver assignment;
- vehicle active/not decommissioned;
- driver active;
- required driver documents valid;
- required vehicle documents valid;
- effective medical check;
- effective technical check;
- no blocking defect;
- no blocking repair;
- no resource conflict.

Результати зберігаються batch-ами й не переписуються.

## 5. Дозвіл диспетчера

Перед `AUTHORIZE` backend виконує **fresh evaluation**, навіть якщо evaluation вже робили кілька хвилин тому.

Це потрібно, бо між evaluate та authorize могли змінитися документи, призначення, дефекти чи validity checks.

Успішна команда атомарно:

- створює authorization;
- фіксує evaluation snapshot;
- переводить Release у `AUTHORIZED`;
- переводить Duty у `AUTHORIZED`;
- створює audit/event/outbox записи;
- створює/перевіряє Waybill відповідно до policy.

## 6. Шляховий лист

До фактичного виїзду система повинна забезпечити required Waybill state.

Waybill отримує:

- унікальний номер;
- template version;
- snapshot business data;
- PDF;
- hashes;
- version history.

Друк не змінює бізнес-дані.

## 7. Фактичний виїзд із депо

Команда `depart Duty` фіксує:

- фактичний час;
- departure odometer;
- fuel, якщо policy вимагає;
- actual vehicle usage;
- actual driver usage.

Передумова — Duty/Release авторизовані.

Після commit:

- Release → `USED`;
- Duty → `ON_LINE`.

## 8. Виконання рейсів

Duty може містити кілька Trips.

Для кожного Trip окремо фіксуються:

- actual departure;
- actual arrival/completion;
- operational events;
- cancellation/deviation, якщо виникло.

Важливо розрізняти:

- виїзд автобуса з депо;
- початок конкретного рейсу;
- завершення конкретного рейсу;
- повернення автобуса в депо.

## 9. Нештатні події

### Поломка автобуса

Не переписуємо первинне призначення.

Система фіксує:

- breakdown event;
- defect;
- завершення actual usage старого автобуса;
- нове призначення/usage нового автобуса;
- effective_at;
- reason;
- audit trail.

### Заміна водія

Аналогічно зберігаються обидва actual usage periods.

### Скасування рейсу

Вимагає reason code/comment відповідно до policy. Скасований рейс не видаляється.

## 10. Повернення в депо

Команда `return Duty` фіксує:

- фактичний час повернення;
- arrival odometer;
- fuel, якщо потрібно.

Guard:

`arrival_odometer >= departure_odometer`.

Duty переходить `ON_LINE → RETURNED`.

## 11. Закриття рейсів

Кожний completed Trip перевіряється окремо.

Перед `CLOSED` обов’язкові:

- actual departure;
- actual arrival;
- логічно коректні timestamps;
- required actual fields;
- відсутність unresolved blocking exception.

При close створюється immutable actual snapshot.

## 12. Закриття Duty

Duty може бути закритий, коли:

- Duty повернувся;
- усі required Trips `CLOSED` або `CANCELLED`;
- odometer/fuel facts достатні;
- unresolved blocking exceptions відсутні;
- Waybill може перейти до фінального closing workflow.

## 13. Закриття Waybill

Фінальна версія містить фактичні дані, template version, snapshot і PDF.

Після `CLOSED` документ не reopen-иться.

Помилка після закриття → correction case → new version.

## 14. Звітність

Після закриття дані повинні одразу бути доступні в operational reports:

- виконані/скасовані рейси;
- фактичний пробіг;
- робота автобуса;
- робота водія;
- statistics release;
- fuel efficiency;
- audit timeline.

## 15. Заборонені shortcut-сценарії

MVP не повинен мати “тимчасових” кнопок:

- `Force close` без business guards;
- `Set status` із довільним dropdown;
- `Ignore conflict` для double-booking;
- `Skip medical/technical check` без формального exception policy;
- `Edit closed`;
- `Delete completed history`.

Якщо підприємству реально потрібен виняток, він моделюється окремою business command із permission, reason і audit, а не прихованим bypass.