# Scope першого production MVP

Перший MVP закриває один наскрізний операційний цикл:

`Автобуси + Водії + Документи → Маршрути/Розклад → Рейси → Duty → призначення ресурсів → передрейсові перевірки → Release → Waybill → фактичний виїзд → виконання рейсів → повернення → закриття → базова звітність`.

## Входить

- Users / RBAC;
- Fleet / Drivers / Documents;
- Stops / Routes / Route Versions;
- Schedules / Trips;
- Duties;
- resource assignments;
- release workflow;
- waybill numbering, PDF and history;
- actual departure/return;
- odometer;
- trip/duty closure;
- audit;
- основні operational reports;
- i18n architecture для `uk/en/es/fr/de`, де українська є мовою за замовчуванням.

## Не входить у перший MVP

GPS, native mobile application, ticketing, payroll, accounting, full spare-parts warehouse, fuel-card integrations та full EDI.
