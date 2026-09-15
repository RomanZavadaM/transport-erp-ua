# Scope першого production MVP

Цей файл є короткою вхідною сторінкою. Детальна канонічна специфікація знаходиться в [`MVP-Definition-Package.md`](MVP-Definition-Package.md).

Перший MVP закриває один повний операційний цикл:

`Автобуси + Водії + Документи → Маршрути/Розклад → Рейси → Duty → призначення ресурсів → передрейсові перевірки → Release → Waybill → фактичний виїзд → виконання рейсів → повернення → закриття → звітність`.

## Входить

- Identity / Users / RBAC;
- Fleet / Drivers / Documents;
- Stops / Routes / Route Versions;
- Schedules / Trips;
- Duty та resource assignments;
- medical / technical / compliance release workflow;
- Waybill numbering, versioned PDF та history;
- actual departure / trip execution / return;
- odometer;
- мінімальний Fuel contour;
- blocking defects, базове ТО і repairs;
- trip/duty/waybill closing;
- corrections без переписування історії;
- audit / operational events;
- основні operational reports;
- production backup/restore/observability;
- i18n architecture для `uk/en/es/fr/de`, де українська є основною та канонічною.

## Не входить у перший MVP

- GPS/live map;
- native mobile application;
- passenger accounting і ticketing;
- payroll;
- accounting;
- full spare-parts warehouse;
- fuel-card integrations;
- full EDI / КЕП workflow;
- external partner API;
- advanced BI/data warehouse.

## Пов’язані документи

- [MVP Definition Package](MVP-Definition-Package.md)
- [Наскрізний робочий день](Operational-Day-Flow.md)
- [Ролі та use cases](Role-Use-Cases.md)
- [Каталог екранів](Screen-Catalog.md)
- [Definition of Done](Definition-of-Done.md)
- [План розробки](Development-Plan.md)

Відсутність post-MVP функцій не є дефектом першого production MVP, якщо наскрізний operational workflow і Definition of Done виконані.