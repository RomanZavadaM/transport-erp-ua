# Release Workspace

Статус: **M0 UX freeze draft**

Release Workspace — сторінка прийняття рішення про випуск конкретного Duty. Вона повинна звести в одному місці **всі факти, що впливають на дозвіл**, без переходів між картками автобуса, водія, документів і перевірок.

## 1. Wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ ← Диспетчерська   Duty D-001   15.09.2026   05:30–15:30      RELEASE_PENDING                 │
│ Маршрут(и): 12 / 101, 104, 109                               [⋯ Історія]                    │
├──────────────────────────────┬───────────────────────────────────────────────────────────────┤
│ РЕСУРСИ                      │ COMPLIANCE                                                    │
│                              │                                                               │
│ Автобус ВС1234АА             │ ✓ Vehicle active                                             │
│ ✓ активний                   │ ✓ Driver active                                              │
│ Одометр 428154               │ ✓ Посвідчення / required docs                                │
│ Документи: ✓  ⚠1            │ ✓ Медконтроль                                                │
│ Defects: немає blocking      │ ✓ Техконтроль                                                │
│                              │ ⚠ Страхування: 3 дні до завершення                           │
│ Водій Іваненко І.І.          │                                                               │
│ ✓ active                     │ Blocking: 0   Warning: 1                                     │
│ Документи: ✓                 │ [Оновити перевірку]                                          │
├──────────────────────────────┼───────────────────────────────────────────────────────────────┤
│ ПЕРЕДРЕЙСОВІ КОНТРОЛІ        │ WAYBILL                                                       │
│ Медичний    ✓ FIT 05:41      │ Draft № / буде присвоєно                                    │
│ Технічний   ✓ PASS 05:48     │ Template: Waybill-UA v3                                     │
│                              │ [Відкрити / сформувати]                                      │
├──────────────────────────────┴───────────────────────────────────────────────────────────────┤
│ ✓ Усі блокуючі правила виконані                                              [Авторизувати] │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Header

Показує:

- Duty number;
- service date/time range;
- Trips/route summary;
- current Release state;
- current aggregate version;
- timeline/history link.

При resource replacement header/card одразу відображає current effective resource, а history доступна окремо.

## 3. Resource cards

### Vehicle card

Показує тільки decision-relevant summary:

- fleet + registration number;
- lifecycle state;
- current assignment period;
- latest confirmed odometer;
- required document summary;
- active blocking defects;
- active blocking repairs;
- shortcut до vehicle card.

### Driver card

- ПІБ;
- personnel identifier, якщо потрібний;
- assignment role/period;
- employment/availability;
- required document summary;
- shortcut до driver card.

Для кількох drivers картки показуються компактним stack/list.

## 4. Document status

Документи групуються:

- required PASS;
- blocking FAIL;
- warnings/expiring soon;
- optional/info.

Наприклад:

```text
Документи автобуса
✓ Реєстраційний документ   до 12.04.2027
✓ ...                      до ...
⚠ ...                      до 18.09.2026 (3 дні)
```

UI не hardcode-ить конкретний regulatory catalog; labels приходять із configured document type/localization.

## 5. Medical / Technical sections

Кожен check показує:

- effective status;
- subject;
- completed_at;
- performer identity в межах permission;
- valid_until, якщо застосовується;
- invalidation indicator;
- link `Переглянути результат`.

Якщо check відсутній:

`Очікує медичного контролю` / `Очікує технічного контролю`.

Диспетчер не отримує поля, які не потрібні для рішення і виходять за projection permission.

## 6. Compliance panel

Показує останній stored evaluation batch.

Групи:

- Blocking FAIL;
- Warning;
- PASS;
- Not applicable.

За замовчуванням PASS-група може бути collapsed, щоб FAIL завжди був зверху.

Кожне правило:

- localized label;
- technical code в details/dev view;
- result;
- subject;
- explanation/details;
- link/action, якщо користувач може усунути причину.

Приклад:

```text
✕ Страхування автобуса прострочене
  VEHICLE_DOCUMENT_VALID
  Автобус: ВС1234АА
  [Відкрити документи автобуса]
```

## 7. Evaluate vs Authorize

`Оновити перевірку` викликає `POST /releases/{id}/evaluate` і створює новий evaluation batch.

`Авторизувати випуск` викликає `POST /releases/{id}/authorize`.

Навіть якщо UI показує PASS, authorize backend робить fresh evaluation.

UI після success не “домальовує” AUTHORIZED локально без response/refetch.

## 8. Authorize confirmation

Коли всі known blocking rules PASS:

```text
Авторизувати випуск Duty D-001?

Автобус: ВС1234АА
Водій: Іваненко І.І.
Медконтроль: PASS 05:41
Техконтроль: PASS 05:48
Blocking rules: 0
Warnings: 1

⚠ Документ ... закінчується через 3 дні.

[Скасувати] [Авторизувати випуск]
```

Warning не ховається confirmation modal-ом.

## 9. Blocked state

Якщо blocking FAIL:

- primary action disabled;
- зверху sticky problem summary;
- кожний FAIL має конкретну причину;
- показуються дозволені resolution links.

Не використовувати просто повідомлення `Випуск неможливий` без причин.

## 10. State progression

UI підтримує state machine:

`OPEN → WAITING_CHECKS → EVALUATING → BLOCKED/READY → AUTHORIZED → USED`.

Користувачу не показується dropdown state.

Actions з'являються відповідно до allowed command + permission.

## 11. Resource changes після check

Якщо після technical check замінено vehicle:

- попередній check не переноситься автоматично на новий vehicle;
- Release Workspace показує required re-check;
- old check/history залишається в timeline.

Аналогічно для driver/medical check.

## 12. Waybill block

Показує:

- чи створено Waybill;
- number/status;
- current version/PDF state;
- чи policy вимагає його до authorize/depart;
- shortcut до Waybill Workspace.

Не генерує PDF автоматично при кожному render сторінки.

## 13. Concurrent change UX

Якщо під час відкритого Workspace інший користувач:

- змінив assignment;
- завершив check;
- додав defect;
- авторизував Release,

SSE показує non-blocking banner:

`Дані оновилися. [Оновити зараз]` або auto-refetch без втрати незбереженого local form.

Перед critical action If-Match гарантує conflict detection.

## 14. Audit/timeline drawer

Показує:

- Duty created;
- vehicle/driver assigned;
- check completed/invalidated;
- evaluation batches;
- authorization/rejection;
- Waybill created;
- departure.

Timeline — read-only.

## 15. Permission-aware UI

Відсутність permission:

- не замінюється disabled кнопкою для всього світу;
- action може не показуватися;
- read-only status залишається, якщо є read permission.

Незалежно від UI backend завжди перевіряє permission.

## 16. Loading/failure

При evaluation/authorize:

- button має pending state;
- повторний click не генерує duplicate command;
- Idempotency-Key reuse дозволяє safe retry;
- при network timeout UI не припускає failure — refetch current Release state.

## 17. Accessibility

- PASS/FAIL не тільки колір;
- collapsible rule groups keyboard accessible;
- confirmation focus trapped correctly;
- blocking summary має heading/alert semantics;
- warnings не озвучуються як successful state.

## 18. Acceptance criteria

- диспетчер може ухвалити рішення, не відкриваючи 5 окремих master-data сторінок;
- всі blocking reasons видно на одному screen;
- current effective vehicle/driver однозначні;
- resource replacement invalidates/requires relevant checks правильно;
- Authorize ніколи не обходить fresh backend evaluation;
- stale If-Match не призводить до silent authorization;
- timeline дозволяє зрозуміти, хто і коли змінив decision context.