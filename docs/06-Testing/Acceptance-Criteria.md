# Acceptance Criteria — архітектурне ядро

Стабільні ID тестів використовуються у traceability matrix.

## Dispatch / concurrency

- **AT-DISPATCH-001** — паралельні конфліктні призначення одного автобуса: рівно одне успішне, інші отримують business conflict.
- **AT-DISPATCH-002** — паралельні конфліктні призначення одного водія блокуються.
- **AT-DISPATCH-003** — один рейс не може мати два active duty membership.
- **AT-CONCURRENCY-001** — застарілий `row_version` повертає conflict замість lost update.
- **AT-CONCURRENCY-002** — повтор одного Idempotency-Key повертає результат тієї ж операції без дубля.

## Release / checks

- **AT-RELEASE-001** — без усіх applicable позитивних передрейсових перевірок випуск не авторизується.
- **AT-RELEASE-002** — blocking FAIL у compliance evaluation блокує випуск.
- **AT-RELEASE-003** — після успішного evaluation зміна blocking condition до `authorize` призводить до відмови, тому що authorization виконує fresh evaluation.
- **AT-RELEASE-004** — effective medical result `FIT` дозволяє пройти medical guard, `UNFIT` блокує Release; інший rigid result code відхиляється schema/domain validation.
- **AT-RELEASE-005** — Release не авторизується без required technical evidence або при blocking technical defect/result.
- **AT-RELEASE-006** — користувач без `technical_check.perform` не може завершити technical check; роль адміністратора сама по собі не дає це permission.

## Compliance / documents

- **AT-COMPLIANCE-001** — однаковий документ може бути required для одного transport/service context і not applicable для іншого; evaluation використовує applicable versioned rule set.
- **AT-COMPLIANCE-002** — carrier-level evidence не помилково зберігається/валідується як driver або vehicle document.
- **AT-COMPLIANCE-003** — історична Release authorization відтворюється з rule version/evaluation snapshot, чинних на момент авторизації, навіть після зміни поточного rule catalog.

## Crew

- **AT-CREW-001** — Duty підтримує двох і більше водіїв із часовими відрізками assignment/actual usage без руйнування Trip/Duty model.
- **AT-CREW-002** — regulatory crew mode не визначається автоматично лише за внутрішнім label `SECOND_DRIVER` або `RELIEF`.
- **AT-CREW-003** — водій, включений в crew одного Duty, все одно не може мати overlapping active assignment в іншому Duty.

## Waybill

- **AT-WAYBILL-001** — конкурентна видача номерів не створює дублікати, а вже виданий номер не reuse-иться.
- **AT-WAYBILL-002** — корекція закритого документа створює нову version і зберігає попередню.
- **AT-WAYBILL-003** — policy одного `PRIMARY` Waybill на Duty може бути застосована без заборони інших explicit document roles/types у майбутньому.

## Service date

- **AT-SERVICE-DATE-001** — зміна company operational-day cutoff/default не змінює `service_date` уже створених Trip/Duty.

## Retention

- **AT-RETENTION-001** — різні document/data classes можуть мати різні retention policies; система не покладається на один global retention value.
- **AT-RETENTION-002** — CLOSED evidence із active legal hold або довшим applicable retention не видаляється purge workflow.
- **AT-RETENTION-003** — object retention policy для фінального документа застосовується за retention class/configuration та не змінює historical document version.

## History / audit

- **AT-HISTORY-001** — закритий Trip snapshot не змінюється після закриття.
- **AT-HISTORY-002** — correction closed Trip створює новий snapshot, не переписуючи старий.
- **AT-AUDIT-001** — кожна визначена critical business command створює audit record з actor/time/entity/action context.
- **AT-AUDIT-002** — runtime role не може UPDATE/DELETE append-only audit/history records.

## i18n

- **AT-I18N-001** — український документ визначений як canonical source для перекладеної сторінки.
- **AT-I18N-002** — зміна locale не змінює API error code або domain status value.

Перед production кожне критичне правило має бути представлене автоматизованим тестом. Regulatory-dependent tests повинні мати fixtures/rule versions, щоб перевіряти історичну відтворюваність рішень.
