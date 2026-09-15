# Localization Testing Matrix

Статус: **M0 i18n contract**

## 1. Locale coverage

Обов'язковий test matrix:

- `uk`;
- `en`;
- `es`;
- `fr`;
- `de`.

`uk` є default/fallback і має найвищий priority для production readiness.

## 2. Resource validation

Автоматично перевіряються:

- required key exists;
- resources parse successfully;
- placeholders match canonical resource;
- unsupported locale falls back to `uk`;
- missing optional key не ламає screen.

## 3. API stability

Для різних locale одна й та сама business error повинна мати однаковий:

```text
error.code
HTTP status
state value
permission code
```

Locale може змінювати presentation text, але не machine contract.

## 4. Date/time/number formatting

Для кожної locale перевіряються:

- date display;
- time display;
- decimal/grouping;
- currency;
- percentages;
- operational timestamps без двозначного day/month interpretation.

## 5. Pluralization

Перевіряються щонайменше values:

```text
0, 1, 2, 4, 5, 11, 21, 22, 25, 101
```

щоб українська та інші locale не використовували спрощену двоформну модель.

## 6. Navigation

Для кожної locale:

- sidebar items visible;
- no clipped critical nav label;
- active route readable;
- breadcrumbs readable;
- permission-driven navigation unchanged semantically.

## 7. Dispatcher Board

Перевіряються:

- headers;
- status labels;
- blocking reasons;
- horizontal overflow;
- sticky columns/header;
- detail drawer;
- empty/loading/error states;
- довгі `de/fr` labels.

## 8. Release Workspace

Перевіряються:

- PASS/WARNING/FAIL labels;
- blocking reason text;
- action buttons;
- stale/concurrent conflict message;
- checklist/readiness sections;
- locale switch без зміни Release state.

## 9. Waybill

Перевіряються:

- selected template locale;
- historical PDF version;
- preview/print конкретної version;
- user locale switch не змінює historical PDF;
- template labels fit print layout;
- page breaks для кожної supported template locale, яка активована.

## 10. Forms

- labels не накладаються на inputs;
- validation messages readable;
- keyboard order не змінюється хаотично;
- buttons visible;
- tables/forms support copy/paste where designed.

## 11. Accessibility

Для кожної production-supported locale перевіряються:

- accessible name кнопок;
- field labels;
- non-color status explanation;
- dialog title/action description;
- language metadata сторінки.

## 12. Visual regression

Для критичних screens рекомендовані screenshot/visual tests принаймні для:

- `uk`;
- найдовшої за layout locale в конкретному screen;
- Waybill print/PDF templates.

## 13. Translation completeness gate

Locale може бути позначена `production-supported`, якщо:

- critical resources complete;
- critical screens pass layout review;
- error/action/status terminology reviewed;
- document templates, якщо вони заявлені для locale, пройшли PDF regression.

## 14. Fallback testing

Навмисно видаляється test key з non-uk locale та перевіряється:

- fallback на `uk`;
- diagnostic signal;
- відсутність raw key у звичайному production UI.
