# Dispatcher Board

Статус: **M0 UX freeze draft**

Головний екран диспетчера — **операційний робочий стіл дня**, а не CRUD-таблиця. Він повинен дозволити за кілька секунд відповісти на питання:

1. що має виїхати найближчим часом;
2. що ще не укомплектовано;
3. що заблоковано і чому;
4. що вже випущено / на лінії / повернулося;
5. де план відрізняється від факту.

## 1. Desktop wireframe

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TransportERP-UA   Диспетчерська    15.09.2026   [Депо: Усі ▼]   [Пошук...]   🔔 12   Роман ▼       │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Проблемні 7] [Без автобуса 2] [Без водія 1] [До випуску 9] [На лінії 14] [Повернулися 18] [Усі] │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Час  Маршрут/рейс  Duty      Автобус      Водій       Док.   Мед.   Тех.   Release   Waybill Факт │
│────────────────────────────────────────────────────────────────────────────────────────────────────│
│06:10  12 / 101      D-001     ВС1234АА     Іваненко     ✓      ✓      ✓      READY     №...    —   │
│06:20  7 / 104       D-002     —             Петренко     —      ✓      —      BLOCKED   —       —   │
│06:30  18 / 108      D-003     ВС7777АА     Коваль       ⚠      ✓      ✓      BLOCKED   draft   —   │
│06:40  5 / 110       D-004     ВС5555АА     Мельник      ✓      ✓      ✓      ON_LINE   №...    +4m │
│ ...                                                                                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 42 рейси • 9 очікують випуск • 7 потребують уваги • оновлено 19:02:14                              │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Layout

### Верхня панель

Містить:

- operational date;
- depot selector;
- global search;
- notification/problem count;
- user/locale menu.

Date/depot є persistent workspace filters: при поверненні з деталей користувач не втрачає контекст.

### Quick filters

Одним кліком:

- `Проблемні`;
- `Без автобуса`;
- `Без водія`;
- `До випуску`;
- `Заблоковані`;
- `На лінії`;
- `Повернулися`;
- `Скасовані`;
- `Усі`.

Кожен filter показує count.

## 3. Основна таблиця

Мінімальні колонки:

- planned departure;
- маршрут / trip number;
- Duty;
- автобус;
- водій/екіпаж;
- документи;
- medical check;
- technical check;
- Release;
- Waybill;
- фактичний стан / delay;
- actions.

### Sticky behavior

На desktop:

- header sticky;
- `Час`, `Маршрут/рейс`, `Duty` можуть бути sticky left;
- actions можуть бути sticky right;
- інші колонки горизонтально scrollable.

Горизонтальна прокрутка повинна бути очевидною та доступною; жодна critical action не повинна опинятися “за межами екрану” без візуального сигналу.

### Density

Default — compact operational density. Користувач може перемкнути `Compact / Comfortable`, але business content не змінюється.

## 4. Рядок Duty/Trip

Клік по рядку відкриває **detail drawer** справа, не руйнуючи позицію у board.

Drawer містить:

- Duty summary;
- trips;
- resource assignments;
- current blocking reasons;
- останні events;
- quick business actions;
- links `Відкрити Duty`, `Відкрити Release`, `Відкрити Waybill`.

Повна окрема сторінка використовується для складного редагування, але швидкий operational triage робиться в drawer.

## 5. Статусні сигнали

Колір ніколи не є єдиним носієм значення.

Приклади:

- `✓ Готовий`;
- `⚠ Документ закінчується через 3 дні`;
- `✕ Страхування прострочено`;
- `✕ Технічний контроль: FAILED`;
- `● На лінії +4 хв`.

При hover/focus на indicator показується коротка причина; click відкриває details.

## 6. Problem priority

Проблеми сортуються за severity та близькістю planned departure.

Наприклад:

1. blocking issue для Duty, який має виїхати за 10 хв;
2. відсутній vehicle/driver для найближчих рейсів;
3. warning document expiry;
4. інформаційне відхилення.

Frontend не вигадує severity — отримує stable problem/rule codes і локалізує label.

## 7. Resource assignment flow

`Призначити автобус` / `Призначити водія` відкриває searchable selector.

Candidate row показує:

- ідентифікатор ресурсу;
- availability;
- найближче assignment;
- critical document indicator;
- depot;
- короткі conflict reasons.

Selector може попередньо відфільтрувати очевидно unavailable candidates, але submit завжди викликає backend command.

При `409 VEHICLE_TIME_CONFLICT` або `DRIVER_TIME_CONFLICT`:

- modal/drawer не закривається;
- показується конфліктний Duty і period;
- список candidates refresh;
- користувач може одразу вибрати інший ресурс.

## 8. Replace resource

Після authorization/on-line не показувати generic `Змінити автобус`.

Показувати command:

`Замінити автобус` / `Замінити водія`.

Форма вимагає:

- effective time;
- replacement resource;
- reason code;
- optional comment.

UI явно показує, що попередня історія не буде стерта.

## 9. Release action

Board не дублює повний Release Workspace.

У рядку показує:

- current state;
- number of blocking failures/warnings;
- shortcut `Відкрити випуск`.

При `READY` може бути швидка кнопка `Авторизувати`, але тільки якщо interaction відкриває короткий confirmation panel із актуальним summary; backend все одно робить fresh evaluation.

Для MVP безпечніший default: авторизація з Release Workspace.

## 10. Realtime updates

Board отримує lightweight SSE events:

- `duty.updated`;
- `trip.updated`;
- `release.updated`;
- `waybill.updated`;
- `assignment.updated`.

Event містить entity id/version, а frontend refetch-ить affected row/detail.

SSE не є consistency mechanism; ETag/DB constraints залишаються authoritative.

## 11. Concurrent edit UX

При `409 CONCURRENT_MODIFICATION`:

```text
Дані цього наряду вже змінив інший користувач.

Було відкрито: версія 21
Поточна версія: 22

[Переглянути зміни] [Оновити дані]
```

Немає кнопки `Все одно зберегти`, яка робить blind overwrite.

## 12. Keyboard workflow

Для desktop power users:

- `/` або defined shortcut → focus search;
- arrows/page navigation у таблиці;
- Enter → detail drawer;
- Esc → close drawer;
- shortcuts не запускають destructive/critical command без confirmation.

Copy text із table/detail повинен працювати звичайним browser способом; компоненти не блокують selection/copy без причини.

## 13. Empty/loading/error states

Loading використовує skeleton/row placeholder без стрибків layout.

Empty state відрізняє:

- `На цю дату рейсів немає`;
- `Фільтр не знайшов результатів`;
- `Рейси ще не згенеровані`.

Network error не очищає already loaded board; показує stale indicator і retry.

## 14. Responsive behavior

### ≥1440 px
Повна operational table.

### 1024–1439 px
Sticky key columns + horizontal scroll; другорядні details приховуються в expandable area.

### <1024 px
Board переходить у simplified list/cards для monitoring, але складне планування/масові assignments позначається як desktop-preferred.

Не намагаємося втиснути 12 колонок у телефон.

## 15. Accessibility

- status не тільки кольором;
- keyboard focus visible;
- icon buttons мають accessible label;
- достатній contrast;
- table semantics або accessible grid;
- confirmations читаються screen reader;
- locale switch не скидає operational context.

## 16. Performance UX

Board не завантажує повні aggregate graphs для всіх рядків.

Використовується optimized list projection; details fetch on demand.

При великому числі rows допускається virtualization, але вона не повинна ламати:

- keyboard navigation;
- copy/select;
- sticky columns;
- screen-reader semantics без окремого accessibility review.

## 17. Acceptance criteria

- диспетчер бачить всі critical блокування без відкривання кожного Duty;
- жодна critical action не схована через overflow;
- current filter/date/depot не губляться після navigation;
- conflict не призводить до silent overwrite;
- board оновлюється після server event;
- причина FAIL видима текстом;
- assign/replace workflow можна пройти без переходу через master-data screens;
- user може копіювати номера, ПІБ та інші дозволені текстові значення стандартними діями браузера.