# MR Policy Decision Register

Статус: **M0 regulatory/business review**  
Дата review: **15.09.2026**

## Статуси

- `CONFIRMED` — правило достатньо підтверджене чинним джерелом для architecture freeze;
- `INTERNAL_POLICY` — законодавство не задає конкретне технічне правило; його затверджує підприємство;
- `CONTEXT_RULE` — правило залежить від виду перевезення/контексту і не може бути глобальним;
- `LEGAL_POLICY` — архітектура готова, але строк/режим має бути затверджений enterprise legal/accounting policy перед production.

## MR-001 — результат щозмінного медичного контролю

**Статус: CONFIRMED**

Рішення:

```text
FIT
UNFIT
```

Форма №137-2/о до наказу №65/80 вимагає чіткого висновку про придатність або непридатність до керування протягом робочої зміни.

Архітектурний наслідок:

- прибрати `FIT_WITH_RESTRICTIONS` із rigid state machine щозмінного pre-trip check;
- `UNFIT` завжди blocking;
- completed result immutable; correction через invalidation + new check.

## MR-002 — Waybill ↔ Duty cardinality

**Статус: INTERNAL_POLICY**

Нормативний review не виявив підстав трактувати історичний «дорожній лист» як універсально обов'язковий документ статті 39 Закону №2344-III. Згадку про дорожній лист із Закону було вилучено.

Рекомендований M0 policy:

- один `PRIMARY` Waybill на Duty як enterprise operational document;
- schema не повинна назавжди блокувати інші document roles/types;
- corrections/versions не є другим незалежним primary document;
- DB uniqueness має враховувати `document_role/type`, а не безумовне `UNIQUE(duty_id)` на всі документи.

Перед migration #1 підприємство має формально підтвердити, що для першого deployment використовується один primary Waybill на Duty.

## MR-003 — crew / кілька водіїв у Duty

**Статус: CONFIRMED + INTERNAL_POLICY DETAIL**

Чинне Положення №340 прямо передбачає керування транспортним засобом в екіпажі щонайменше двома водіями.

Підтверджено:

- schema повинна підтримувати кількох водіїв;
- resource conflict одного водія між різними Duty залишається жорстким інваріантом;
- actual driver usage зберігається часовими відрізками.

Внутрішні labels `PRIMARY`, `SECOND_DRIVER`, `RELIEF`, `TRAINEE` є enterprise/UI semantics і не повинні підміняти нормативне поняття crew mode.

Рекомендація:

- додати `crew_mode` / policy context для Duty або execution segment;
- не ставити DB constraint «рівно один PRIMARY водій на весь Duty» як нормативний інваріант.

## MR-004 — required/blocking documents

**Статус: CONTEXT_RULE**

Стаття 39 Закону №2344-III задає різні документи залежно від виду пасажирського перевезення. Для регулярних перевезень перелік водія включає посвідчення відповідної категорії, реєстраційні документи, квитково-касовий лист, схему маршруту, розклад, таблицю вартості проїзду для неміських перевезень та інші визначені законодавством документи.

Висновок:

- не seed-ити один global document catalog `required_for_release=true` для всіх перевезень;
- compliance rules повинні враховувати `service/transport type`, route type і applicable rule version;
- driver license/category та vehicle registration є базовими checks;
- route/schedule/fare artifacts перевіряються за контекстом;
- carrier-level license/contract/route-passport evidence не слід насильно моделювати як `driver_document` або `vehicle_document`.

## MR-005 — operational day cutoff

**Статус: INTERNAL_POLICY**

Нормативні акти регулюють робочий час, керування, відпочинок, розклад і service operation, але M0 не виявив універсальної вимоги, що календарний operational day транспортної системи має переключатися, наприклад, о 03:00.

Рішення:

- `service_date` є explicit immutable planning attribute;
- optional `operational_day_cutoff` — setting підприємства;
- зміна cutoff не переобчислює історичні `service_date`;
- default policy до окремого рішення: календарний день у `Europe/Kyiv`, без штучного cutoff.

## MR-006 — формат і скидання номера Waybill

**Статус: INTERNAL_POLICY**

Оскільки Waybill у нашій M0-моделі є enterprise operational/accounting document, не знайдено універсального чинного державного формату номера, який треба hardcode-ити для всіх таких документів.

Рішення architecture freeze:

- `number_sequences` залишається універсальним;
- підтримує series/year/prefix/suffix/next_value;
- вже виданий номер не reuse-иться;
- default reset policy не зашивається в DB.

Рекомендований deployment default: окрема серія на тип документа + рік, якщо підприємство не затвердить інше.

## MR-007 — retention / object lock

**Статус: LEGAL_POLICY**

Підтверджено:

- строки залежать від класу документа;
- Перелік №578/5 задає мінімальні архівні строки;
- Податковий кодекс для відповідної категорії первинних документів юридичних осіб передбачає мінімум 1825 днів, якщо не застосовується довший строк;
- строки можуть продовжуватися за умовами законодавства/перевірок/інших підстав.

Architecture freeze decision:

- retention configurable by document/data class;
- closed Waybill/history не auto-delete;
- `legal_hold`/extended retention повинні бути можливими;
- object-lock/retention duration не hardcode-иться до enterprise legal/accounting retention matrix.

До production launch потрібна окрема затверджена retention matrix.

## Додаткове рішення — технічний checker

За результатами review наказу №974:

- БД/API використовують neutral concept `technical_checker` / authorized qualified person;
- UI role «Механік» — role profile підприємства, а не нормативна назва єдиного допустимого виконавця;
- driver pre-departure technical check зберігається окремим evidence;
- blocking defect/result блокує Release.

## Додаткове рішення — route passport external identity

Після набрання чинності новим Порядком у 2026 році паспорт маршруту формується через державний Єдиний комплекс.

У майбутньому для route/passport integration потрібні:

- external system code;
- external passport identifier;
- QR/verification reference;
- sync status/timestamp;
- official artifact/reference.

Ці поля/таблиці можуть бути додані окремою backward-compatible migration до інтеграційного модуля; M0 domain schema не повинна дублювати державну систему як власне source of truth.
