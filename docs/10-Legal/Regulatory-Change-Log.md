# Regulatory Change Log

Канонічна мова: українська.

## 15.09.2026 — M0 regulatory baseline

### Перевірені джерела

- Закон України «Про автомобільний транспорт» №2344-III;
- наказ МОЗ/МВС №65/80 (`z0308-13`);
- наказ №974 (`z0794-08`);
- Положення №340 (`z0811-10`) із актуальними змінами 2025–2026 років;
- наказ Мінрозвитку №1473 (`z1924-25`), чинний у новому механізмі з 13.07.2026;
- Перелік Мін'юсту №578/5 (`z0571-12`);
- Податковий кодекс України, стаття 44.

### Architecture-impact decisions

- щозмінний medical result нормалізовано до `FIT/UNFIT`;
- technical check executor у domain model — qualified/authorized checker, а не одна hardcoded job title;
- driver pre-departure technical evidence виділяється окремо;
- document compliance стає context/version-aware;
- crew mode підтримує кількох водіїв і не ототожнюється з UI labels;
- Waybill не моделюється як універсально обов'язковий державний «дорожній лист»;
- Waybill cardinality/numbering — enterprise policy поверх versioned document model;
- route passport integration розглядається як external government integration boundary;
- retention — class-based; один global retention period заборонений.

### Watch list

Перед implementation/release необхідно повторно перевіряти джерело, якщо зміни стосуються:

- документів водія/перевізника;
- медичних оглядів;
- технічного контролю;
- режиму праці/відпочинку;
- route passport / державного Єдиного комплексу;
- строків зберігання та первинних документів.

### Review trigger

Regulatory impact review запускається при:

- новій редакції джерела зі списку вище;
- зміні виду перевезень, що підтримує deployment;
- додаванні міжнародних/нерегулярних/таксі workflows;
- появі електронного документообігу або підпису;
- інтеграції з державними реєстрами;
- зміні retention/legal-hold policy.

## Формат наступних записів

Кожна зміна повинна містити:

- дату виявлення;
- джерело та нову редакцію;
- affected `BR-*` / `AT-*`;
- impact: `NONE`, `CONFIG`, `RULE`, `API`, `DB`, `DOCUMENT_TEMPLATE`;
- migration/backfill need;
- effective date;
- відповідального за review.
