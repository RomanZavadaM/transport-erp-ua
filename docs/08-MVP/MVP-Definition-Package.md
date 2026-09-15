# MVP Definition Package

Статус: **M0 / Architecture Freeze — draft for review**  
Канонічна мова: **українська**  
Пов’язаний issue: **#1**

## 1. Мета першого production MVP

Перший MVP повинен забезпечити **повний наскрізний виробничий цикл транспортного підприємства**, а не набір незалежних довідників.

Критерій цінності MVP: підприємство може запланувати робочий день, сформувати рейси та наряди, призначити автобуси і водіїв, провести необхідні передрейсові контролі, дозволити випуск, сформувати шляховий лист, зафіксувати фактичний виїзд і повернення, закрити виконані рейси та отримати базову операційну звітність.

Основний цикл:

`Довідники → Розклад → Рейси → Duty → Ресурси → Контролі → Release → Waybill → Виїзд → Виконання → Повернення → Закриття → Звіти`

## 2. Межа MVP

### 2.1. Обов’язково входить

1. **Identity / Access**
   - користувачі;
   - ролі;
   - permissions;
   - безпечна автентифікація;
   - аудит критичних дій.

2. **Fleet**
   - автобуси;
   - життєвий статус;
   - документи автобуса;
   - одометр;
   - блокуючі дефекти;
   - базова історія.

3. **Drivers**
   - водії;
   - статус зайнятості;
   - документи;
   - необхідні категорії/допуски;
   - історія змін.

4. **Routes / Stops**
   - зупинки;
   - маршрути;
   - версії маршрутів;
   - напрямки;
   - послідовність зупинок;
   - планова відстань.

5. **Schedules / Trips**
   - версії розкладу;
   - календарі роботи;
   - регулярні відправлення;
   - генерація рейсів;
   - нерегулярний/додатковий рейс;
   - скасування рейсу з причиною.

6. **Duty / Dispatch**
   - створення наряду;
   - включення 1..N рейсів;
   - призначення автобуса;
   - призначення водія/водіїв;
   - захист від часових конфліктів;
   - заміна ресурсу без стирання історії;
   - dispatcher board.

7. **Release**
   - перевірка необхідних документів;
   - медичний контроль;
   - технічний контроль;
   - compliance evaluation;
   - блокування при критичному FAIL;
   - дозвіл диспетчера;
   - незмінна історія рішення.

8. **Waybill**
   - номер;
   - серія/послідовність;
   - versioned template;
   - snapshot даних;
   - PDF;
   - друк;
   - повернення;
   - закриття;
   - correction workflow без silent rewrite.

9. **Execution / Actuals**
   - фактичний виїзд із депо;
   - початок/завершення рейсів;
   - фактичне повернення;
   - одометр при виїзді/поверненні;
   - фактичний пробіг;
   - базові операційні події;
   - trip/duty close.

10. **Fuel — мінімальний контур**
    - операція заправки/видачі;
    - прив’язка до автобуса;
    - опційна прив’язка до Duty/Waybill;
    - кількість літрів;
    - одометр;
    - базова витрата л/100 км.

11. **Maintenance — мінімальний контур**
    - блокуючий дефект;
    - базове ТО;
    - ремонтний наряд;
    - статус ремонту;
    - ознака `blocks_operation`.

12. **Reports**
    - рейси за день/період;
    - робота автобуса;
    - робота водія;
    - пробіг;
    - скасовані рейси;
    - статистика випуску;
    - паливо і л/100 км;
    - прострочені документи;
    - базові ТО/ремонти.

13. **Platform**
    - PostgreSQL migrations;
    - backup/restore;
    - structured logs;
    - health checks;
    - CI/CD;
    - object storage для PDF/вкладень;
    - локалізації `uk/en/es/fr/de`, де `uk` — default/canonical.

### 2.2. Свідомо не входить у MVP

- GPS ingestion і GPS tracks;
- live map/online monitoring;
- native mobile application;
- повний passenger accounting;
- ticketing / e-ticket;
- зарплата;
- бухгалтерський облік;
- повний склад запчастин;
- автоматична інтеграція з паливними картками;
- повний електронний документообіг з КЕП;
- зовнішній public API для партнерів;
- складний BI/data warehouse.

Ці функції **не реалізуються**, але архітектура MVP не повинна їх блокувати.

## 3. Ролі MVP

Обов’язкові робочі ролі:

- **Керівник** — dashboard, reports, audit/read-only контроль;
- **Диспетчер** — планування operational day, Duty, призначення, release authorization, waybill workflow, фактичний рух і закриття;
- **Механік** — technical check, defects, maintenance/repair;
- **Медик** — medical check;
- **Водій** — read-only власне завдання та мінімальні власні дії, якщо включено в deployment;
- **Адміністратор** — users, roles, permissions, settings, templates, dictionaries;
- **Системний сервіс/worker** — PDF, report exports, outbox, integrity checks.

## 4. Ключові інваріанти MVP

MVP не може бути прийнятий, якщо система допускає хоча б один із станів:

- один автобус одночасно має два overlapping active assignments;
- один водій одночасно має два overlapping active assignments;
- один Trip одночасно належить двом активним Duty;
- Release авторизований без чинного required medical check;
- Release авторизований без чинного required technical check;
- Release авторизований при blocking document failure, defect або repair;
- closed Trip фізично видалений або непомітно переписаний;
- closed Waybill фізично видалений або його стара версія переписана;
- два Waybill отримали однаковий business number;
- concurrent update непомітно перетер дані іншого користувача;
- critical business command не залишила audit trail.

## 5. Мінімальні operational reports

До production MVP належать саме операційні, а не BI-звіти:

1. Рейси за день.
2. Рейси за період.
3. Невипущені / заблоковані Duty.
4. Статистика випуску.
5. Скасовані рейси та причини.
6. Робота автобуса за період.
7. Робота водія за період.
8. Пробіг по автобусах.
9. Паливо та л/100 км.
10. Документи, що прострочені або скоро закінчуються.
11. Автобуси з активними blocking defects/repairs.
12. Базова історія Waybill/Release/Audit для конкретного Duty.

## 6. Залежності модулів

```text
Identity/RBAC ─────────────────────────────────────────────┐
Fleet + Drivers + Documents ─┐                            │
Routes + Stops ───────────────┼→ Planning → Trips          │
Schedules ────────────────────┘              ↓             │
                                         Dispatch/Duty     │
                                              ↓            │
                         Technical + Medical + Compliance  │
                                              ↓            │
                                           Release         │
                                              ↓            │
                                           Waybill         │
                                              ↓            │
                                         Execution         │
                                              ↓            │
                                     Closing/Corrections   │
                                              ↓            │
                                      Reports / Audit  ←───┘
```

Maintenance і Fuel використовують Fleet як базовий контекст, але не повинні створювати циклічну залежність на рівні domain modules.

## 7. Production readiness MVP

MVP означає **production-ready minimum**, а не demo.

Обов’язкові нефункціональні характеристики:

- HTTPS;
- RBAC на backend;
- захист від cross-company access;
- password hashing;
- secure session/token strategy;
- CSRF/XSS/SQL injection protections;
- rate limiting для критичних public/auth endpoint;
- optimistic concurrency;
- DB constraints на фундаментальні інваріанти;
- idempotency critical commands;
- append-only audit;
- backup + WAL/PITR policy;
- перевірений restore;
- structured logging;
- health/readiness checks;
- automated test suite;
- migrations versioned in Git;
- no production secrets in repository.

## 8. Умови завершення M0

До початку Alembic migration #1 та application code повинні бути погоджені:

- цей MVP Definition Package;
- user flows / operational day;
- screen catalog;
- role/use-case matrix;
- OpenAPI MVP contract;
- PostgreSQL physical schema design;
- permissions matrix;
- Definition of Done;
- testing strategy;
- deployment/backup/DR design;
- i18n contract.

## 9. Принцип зміни scope

Після Architecture Freeze будь-яке розширення MVP повинно мати:

1. GitHub Issue;
2. business rationale;
3. impact analysis на DB/API/UX/tests;
4. ADR, якщо змінюється архітектурне рішення;
5. явне рішення: `MVP`, `post-MVP` або `rejected`.

Не допускається приховане розширення scope “по ходу реалізації”.