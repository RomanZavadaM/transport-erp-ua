# Навігація та інформаційна архітектура WEB-інтерфейсу

Статус: **M0 UX freeze draft**

## 1. Основне меню

Канонічна українська структура:

```text
Dashboard
Автобуси
Водії
Маршрути
Розклад
Рейси
Випуск
Шляхові листи
Рух
Паливо
ТО та ремонти
Документи
Звіти
Користувачі
Аудит
Налаштування
```

Видимість визначається effective permissions.

## 2. Логічне групування sidebar

Рекомендоване desktop grouping:

```text
Огляд
  Dashboard

Планування
  Маршрути
  Розклад
  Рейси

Операції
  Диспетчерська / Duty
  Випуск
  Шляхові листи
  Рух

Ресурси
  Автобуси
  Водії
  Документи

Експлуатація
  Паливо
  ТО та ремонти

Аналітика
  Звіти
  Аудит

Система
  Користувачі
  Налаштування
```

Назва `Диспетчерська` може бути primary menu label для Duty workspace, тоді як `Duty` лишається technical/domain term у документації/API.

## 3. URL structure

```text
/dashboard

/fleet/vehicles
/fleet/vehicles/{id}

/drivers
/drivers/{id}

/routes
/routes/{id}
/routes/{id}/versions/{version_id}

/schedules
/schedules/{id}

/operations/trips
/operations/trips/{id}
/operations/duties
/operations/duties/{id}

/release
/release/{id}

/waybills
/waybills/{id}

/movement

/fuel

/maintenance/defects
/maintenance/plans
/maintenance/repairs
/maintenance/repairs/{id}

/documents
/reports
/audit

/admin/users
/admin/roles
/admin/settings
/admin/templates
```

URL не залежить від UI locale. Locale може зберігатися preference/cookie/context, щоб зміна мови не ламала deep links.

## 4. Dashboard vs workspace

Dashboard — огляд і drill-down.

Operational workspace — місце роботи.

Не переносити складні operational forms у Dashboard widgets.

## 5. Breadcrumbs

Для detail screens:

`Диспетчерська / Duty D-001 / Випуск`

`Автобуси / ВС1234АА / Документи`

`Маршрути / 12 / Версія 4`

Breadcrumb не дублює browser back; він показує domain hierarchy.

## 6. Master data vs operations

Критично розрізняти:

- `Автобуси` — master/history card;
- `Диспетчерська` — призначення автобуса на Duty;
- `Водії` — master/history card;
- `Диспетчерська` — призначення водія;
- `Маршрути/Розклад` — планування;
- `Рух` — current фактичне виконання.

Operational user не повинен редагувати master entity лише для виконання щоденної команди.

## 7. Context preservation

При переході:

`Dispatcher Board → Release Workspace → назад`

зберігаються:

- service date;
- depot;
- active filter;
- sort;
- scroll/selected row where technically reasonable.

Це може бути URL query state або controlled workspace state.

## 8. Deep linking

Кожна business entity/detail screen має stable URL.

Посилання з Audit/Report/Notification відкриває entity напряму, але backend permission/tenant check застосовується заново.

## 9. Global search

MVP global search може шукати по дозволених ідентифікаторах:

- vehicle fleet/registration number;
- driver name/personnel number;
- Duty number;
- Trip number;
- Waybill number.

Search results permission-filtered; не розкривають existence чужого tenant.

## 10. Command placement

Primary business commands знаходяться у відповідному workspace, а не в глобальному menu.

Наприклад:

- `Авторизувати випуск` — Release Workspace;
- `Закрити Waybill` — Waybill Workspace;
- `Complete Repair` — Repair Workspace.

## 11. Tabs inside cards

Vehicle/Driver cards можуть мати tabs:

Vehicle:

- Огляд;
- Документи;
- Одометр;
- Duty/рейси;
- Дефекти;
- ТО;
- Ремонти;
- Історія.

Driver:

- Огляд;
- Документи;
- Duty/рейси;
- Історія.

Tab state може бути частиною URL, щоб deep links працювали.

## 12. Mobile/tablet navigation

Desktop — persistent sidebar.

Tablet — collapsible sidebar.

Phone — drawer/bottom-level navigation only for meaningful mobile/read workflows; не намагаємося перенести всю admin/disptacher desktop IA у bottom navigation.

## 13. Locale switch

Locale switch у user menu/header:

- `Українська`;
- `English`;
- `Español`;
- `Français`;
- `Deutsch`.

Current route/query/filter зберігаються.

## 14. Permission-aware navigation

Sidebar не є security boundary, але не показує недоступні секції.

При direct URL без permission:

- backend → 403;
- frontend → access denied page, без leakage details.

При missing tenant entity:

- 404 semantics відповідно до API contract.

## 15. Audit/history navigation

Entity card має link `Історія`, але не всі ролі бачать raw audit.

Read model timeline може бути доступний ширше, raw audit search — лише відповідним permissions.

## 16. Acceptance criteria

- primary menu відповідає business areas, а не DB tables;
- одна сутність має stable detail URL;
- operational flow не втрачає date/depot/filter context;
- locale не змінює URLs/domain identifiers;
- permission changes відображаються в navigation;
- deep links безпечні;
- master-data та operational actions чітко розділені.