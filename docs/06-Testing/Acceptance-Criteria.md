# Acceptance Criteria — архітектурне ядро

Стабільні ID тестів використовуються у traceability matrix.

- **AT-DISPATCH-001** — паралельні конфліктні призначення одного автобуса: рівно одне успішне, інші отримують business conflict.
- **AT-DISPATCH-002** — паралельні конфліктні призначення одного водія блокуються.
- **AT-DISPATCH-003** — один рейс не може мати два active duty membership.
- **AT-RELEASE-001** — без обов'язкових позитивних перевірок випуск не авторизується.
- **AT-RELEASE-002** — blocking FAIL у compliance evaluation блокує випуск.
- **AT-WAYBILL-001** — конкурентна видача номерів не створює дублікати.
- **AT-WAYBILL-002** — корекція закритого документа створює нову version і зберігає попередню.
- **AT-HISTORY-001** — закритий trip snapshot не змінюється після закриття.
- **AT-HISTORY-002** — correction closed trip створює новий snapshot, не переписуючи старий.
- **AT-CONCURRENCY-001** — застарілий `row_version` повертає conflict замість lost update.
- **AT-CONCURRENCY-002** — повтор одного Idempotency-Key повертає результат тієї ж операції без дубля.
- **AT-I18N-001** — український документ визначений як canonical source для перекладеної сторінки.
- **AT-I18N-002** — зміна locale не змінює API error code або domain status value.

Перед production кожне критичне правило має бути представлене автоматизованим тестом.
