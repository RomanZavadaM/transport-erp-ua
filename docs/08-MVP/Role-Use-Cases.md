# Ролі та ключові use cases MVP

Статус: **M0 draft**

Цей документ описує бізнес-можливості ролей. Реальні дозволи реалізуються через permissions, а не через hardcoded `if role == ...`.

## 1. Керівник

Мета: бачити стан підприємства без втручання в операційну історію.

Ключові use cases:

- переглянути dashboard за день;
- побачити заплановано / випущено / на лінії / завершено / скасовано;
- переглянути блокування випуску;
- переглянути utilization автобусів;
- переглянути роботу водіїв;
- переглянути пробіг і паливо;
- переглянути прострочені документи;
- переглянути ТО/ремонти;
- відкрити audit timeline конкретного Duty/Trip/Waybill;
- експортувати дозволені звіти.

Керівник за замовчуванням не отримує універсального права редагувати operational history.

## 2. Диспетчер

Мета: організувати і провести operational day.

Ключові use cases:

- переглянути рейси дня;
- створити додатковий/нерегулярний рейс;
- скасувати рейс з причиною;
- створити Duty;
- додати/видалити рейс із незапущеного Duty;
- призначити автобус;
- призначити водія/екіпаж;
- побачити resource conflict;
- замінити автобус/водія контрольованою командою;
- відкрити Release Workspace;
- побачити стан документів, медичного і технічного контролю;
- запустити compliance evaluation;
- авторизувати випуск, якщо guards PASS;
- сформувати/видати Waybill;
- зафіксувати departure/return у дозволеному deployment workflow;
- контролювати рейси на лінії;
- зареєструвати delay/breakdown/manual note;
- завершити/закрити Trip;
- закрити Duty;
- закрити Waybill;
- переглянути історію дій.

Диспетчер не може сам створити позитивний medical або technical check, якщо не має окремого permission.

## 3. Механік

Мета: підтвердити технічну готовність автобуса та вести мінімальний контур дефектів/ремонтів.

Ключові use cases:

- побачити чергу автобусів на технічний контроль;
- відкрити призначений автобус і Duty;
- внести odometer;
- пройти versioned checklist;
- зафіксувати PASSED/FAILED;
- створити defect із severity/blocks_release;
- invalidate помилково завершений check із причиною;
- створити/оновити maintenance event;
- створити repair order;
- перевести repair за state machine;
- завершити/verify repair;
- бачити історію дефектів автобуса.

Completed technical check не редагується in-place.

## 4. Медик

Мета: зафіксувати результат передрейсового медичного контролю з мінімально необхідною обробкою персональних даних.

Ключові use cases:

- побачити чергу водіїв, яким потрібен контроль;
- ідентифікувати водія і Duty;
- зафіксувати `FIT / UNFIT / FIT_WITH_RESTRICTIONS`, якщо така модель буде затверджена;
- встановити validity, якщо policy це передбачає;
- додати дозволений коментар;
- invalidate помилковий check із причиною;
- переглянути власну історію перевірок у межах permission.

Система не повинна вимагати зберігання медичного діагнозу, якщо він не потрібний для транспортного workflow.

## 5. Водій

MVP роль водія є мінімальною і може бути deployment-configurable.

Ключові use cases:

- переглянути власний Duty;
- побачити автобус, маршрути, рейси і час;
- відкрити власний Waybill у дозволеному форматі;
- повідомити про defect/incident, якщо ця функція ввімкнена;
- переглянути власні фактичні рейси.

Водій не бачить дані інших водіїв і не отримує адміністративні/диспетчерські можливості.

## 6. Адміністратор

Мета: керувати платформою, а не підміняти бізнес-ролі.

Ключові use cases:

- створити/disable користувача;
- керувати ролями і permissions;
- налаштувати company/depot settings;
- керувати document/check templates;
- керувати довідниками;
- налаштувати numbering policy;
- налаштувати locale defaults;
- переглядати технічний стан інтеграцій/worker за дозволом.

Адміністратор не отримує автоматично права `release.authorize`, `medical_check.perform`, `technical_check.perform` чи можливість переписувати closed history.

## 7. Системний worker

Не є людською роллю.

Use cases:

- рендер PDF;
- формування важких report exports;
- публікація outbox events;
- integrity checks;
- планові технічні jobs;
- lifecycle cleanup короткоживучих технічних даних.

Worker використовує окрему service identity та мінімальні DB/API permissions.

## 8. Separation of Duties

Архітектура повинна дозволяти policy, за якою:

- медичний check і release authorization виконують різні суб’єкти;
- technical check і release authorization виконують різні суб’єкти;
- correction closed history може вимагати окремого approval permission;
- administrator не прирівнюється до super-business-user.

Для невеликого підприємства policy може бути м’якшою, але кожна критична дія все одно повинна мати actor, timestamp, permission і audit.

## 9. Мінімальна permission matrix

| Операція | Керівник | Диспетчер | Механік | Медик | Водій | Admin |
|---|---|---|---|---|---|---|
| Перегляд рейсів | R | RW | R-min | R-min | own | R |
| Duty / assignments | R | RW | R | R-min | own | config |
| Medical check | - | result | - | RW | own result | - |
| Technical check | R | result | RW | - | - | - |
| Release authorize | R | RW | - | - | - | - |
| Waybill | R | RW | R | - | own | templates |
| Defects / repairs | R | R | RW | - | report | config |
| Reports | R | R | limited | limited | own | R |
| Audit | R | limited | own | own | own | R |
| Users/RBAC | - | - | - | - | - | RW |

`R-min` означає спеціальну projection із мінімальним набором полів.