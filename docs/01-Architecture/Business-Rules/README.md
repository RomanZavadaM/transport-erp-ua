# Каталог бізнес-правил

Кожне правило має стабільний ID. ID не перекладається та не змінюється при редагуванні формулювання.

## Dispatch

- **BR-DISPATCH-001** — один автобус не може мати два активні призначення, що перекриваються в часі.
- **BR-DISPATCH-002** — один водій не може мати два активні призначення, що перекриваються в часі.
- **BR-DISPATCH-003** — один рейс не може одночасно входити до двох активних нарядів.

## Release

- **BR-RELEASE-001** — випуск можливий лише при позитивних обов'язкових передрейсових перевірках.
- **BR-RELEASE-002** — blocking compliance rule із результатом FAIL забороняє авторизацію випуску.
- **BR-RELEASE-003** — авторизація повторно перевіряє актуальний стан, а не покладається на старий результат evaluation.
- **BR-RELEASE-004** — для щозмінного медичного контролю ефективний результат `FIT` є обов'язковою умовою випуску; `UNFIT` завжди блокує Release.
- **BR-RELEASE-005** — технічна готовність до виїзду повинна мати позитивний результат уповноваженої технічної перевірки та передвиїзне evidence перевірки технічного стану водієм відповідно до застосовного workflow.
- **BR-RELEASE-006** — виконавця технічної перевірки визначає permission/кваліфікація (`technical_check.perform`), а не жорстко зашита назва посади «механік».

## Compliance / Documents

- **BR-COMPLIANCE-001** — перелік required/blocking документів визначається контекстом виду перевезення, маршруту та чинної версії compliance rule, а не одним глобальним списком для всіх Duty.
- **BR-COMPLIANCE-002** — carrier-level evidence (ліцензія, договір/дозвіл, паспорт маршруту та подібні підстави) не підмінюється записами `driver_document` або `vehicle_document`.
- **BR-COMPLIANCE-003** — нормативно залежні compliance rules мають effective period/version, щоб історичне рішення Release можна було відтворити за правилами, чинними на момент рішення.

## Crew / Driver Work

- **BR-CREW-001** — Duty та фактичне виконання повинні підтримувати кількох водіїв і часові відрізки їх роботи; модель не припускає рівно одного водія на весь Duty.
- **BR-CREW-002** — regulatory crew mode є окремим поняттям від внутрішніх labels `PRIMARY`, `SECOND_DRIVER`, `RELIEF`, `TRAINEE`.
- **BR-CREW-003** — заборона overlapping assignments одного водія між Duty діє незалежно від crew mode.

## Waybill

- **BR-WAYBILL-001** — виданий номер шляхового листа є унікальним і не використовується повторно.
- **BR-WAYBILL-002** — закрита версія документа не редагується; виправлення створює нову версію.
- **BR-WAYBILL-003** — Waybill є versioned enterprise operational/accounting document; requiredness, document role/cardinality та numbering policy є конфігурованими policy, якщо конкретна чинна норма не встановлює жорсткіше правило.

## Service Date

- **BR-SERVICE-DATE-001** — `service_date` фіксується явно й не переобчислюється заднім числом після зміни company operational-day settings.

## Retention

- **BR-RETENTION-001** — строки зберігання задаються за класом даних/документа; один глобальний `retention_days` для всіх сутностей заборонений.
- **BR-RETENTION-002** — CLOSED business history не видаляється автоматично лише через досягнення мінімального строку; legal hold, перевірка або довший applicable строк можуть продовжити retention.
- **BR-RETENTION-003** — object-lock/physical-retention policy для фінальних документів походить із затвердженої enterprise retention matrix.

## History / Audit

- **BR-HISTORY-001** — закритий рейс не змінює попередній snapshot фактичних даних.
- **BR-HISTORY-002** — корекція закритого факту створює новий snapshot із посиланням на попередній.
- **BR-AUDIT-001** — критичні бізнес-команди створюють audit record.
- **BR-AUDIT-002** — audit та історичні event records не видаляються прикладним workflow.

## Concurrency

- **BR-CONCURRENCY-001** — lost update блокується optimistic locking.
- **BR-CONCURRENCY-002** — повтор критичної команди з тим самим Idempotency-Key не створює дубль операції.

## Language / i18n

- **BR-I18N-001** — українська є канонічною мовою бізнес-вимог.
- **BR-I18N-002** — локалізація не змінює machine-readable business codes і status values.
