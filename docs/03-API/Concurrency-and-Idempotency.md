# Конкурентність та ідемпотентність API

Статус: **M0 draft**

## 1. Мета

Система повинна коректно працювати при одночасній роботі кількох диспетчерів і повторних HTTP requests через double click, retry browser/proxy або нестабільну мережу.

## 2. Optimistic locking

Mutable aggregate має `row_version`.

API повертає:

`ETag: "42"`

Mutation клієнта:

`If-Match: "42"`

Якщо актуальна версія вже `43`, backend повертає:

- HTTP `409`;
- `CONCURRENT_MODIFICATION`;
- актуальну version/reference у `details` за потреби.

Backend не робить last-write-wins для критичних aggregate.

## 3. Де If-Match обов'язковий

Мінімально:

- Duty commands, які залежать від current state;
- Release authorization;
- Waybill issue/close;
- Trip close;
- repair order transitions;
- update critical mutable master data.

Create operations не потребують If-Match.

## 4. DB locking

Optimistic lock не замінює DB constraints/row locks.

Короткі критичні транзакції використовують `SELECT ... FOR UPDATE`/equivalent для aggregate root і deterministic lock ordering.

Типовий порядок:

`Duty → Trips → resource state/assignments → Release → Waybill → Number Sequence`.

## 5. Resource allocation

Перед assign API може виконати availability query, але остаточна гарантія — PostgreSQL exclusion constraint.

Сценарій двох одночасних assign requests:

1. обидва бачать vehicle як available;
2. обидва надсилають command;
3. один INSERT commit успішний;
4. другий отримує exclusion violation;
5. backend перетворює його на `409 VEHICLE_TIME_CONFLICT`.

UI ніколи не є source of truth availability.

## 6. Idempotency-Key

Required для command, повторне виконання якої може створити duplicate side effects.

Мінімально:

- release authorize;
- waybill create/issue/generate, де створюється persistent artifact/number;
- trip close;
- duty close;
- report export create;
- інші commands, визначені implementation review.

## 7. Semantics Idempotency-Key

Scope key:

`company_id + authenticated actor/client + endpoint/command + key`.

При першому request backend зберігає:

- key;
- normalized request hash;
- status/result reference;
- response status/body або достатній replay descriptor;
- created/expires timestamps.

Повтор із тим самим key і тим самим normalized payload повертає той самий логічний результат без повторного side effect.

Повтор із тим самим key, але іншим payload:

`409 IDEMPOTENCY_KEY_REUSED`.

## 8. TTL

Idempotency record не зберігається безкінечно.

Точний TTL — deployment/application setting; для critical document/financial-like operations він має бути достатнім, щоб покрити реальні network retries.

Business uniqueness constraints залишаються постійним захистом навіть після expiry idempotency record.

## 9. Waybill numbering

Idempotency не є єдиним захистом numbering.

Number allocation окремо захищена:

- row lock number sequence;
- atomic increment;
- unique DB constraint на business number.

Повторний request із тим самим Idempotency-Key повертає вже створений Waybill, а не бере новий номер.

## 10. Release authorization

Два одночасні authorize requests:

- один бере lock/перемагає;
- створює єдиний positive authorization;
- другий після очікування бачить новий state;
- з тим самим idempotency key отримує replay success;
- з іншим key отримує `RELEASE_ALREADY_AUTHORIZED`, якщо semantics не визначають equivalent success.

DB має unique invariant для positive authorization.

## 11. Retry transient DB errors

Backend може автоматично retry:

- serialization failure;
- deadlock detected;

лише для transaction, де side effects захищені transaction boundary/idempotency.

Retry count bounded; нескінченні retries заборонені.

## 12. External side effects

PDF/object storage/outbound integration не повинні створювати non-transactional inconsistency.

Для integration events використовується transactional outbox.

Для PDF generation:

- business version/snapshot створюється контрольовано;
- worker job має stable identity;
- duplicate job не створює нову document version без business command.

## 13. Frontend behavior

При `CONCURRENT_MODIFICATION` frontend:

1. не повторює mutation blind retry;
2. refetch aggregate;
3. показує, що дані змінилися іншим користувачем;
4. просить повторити business decision на актуальних даних.

При `VEHICLE_TIME_CONFLICT`/`DRIVER_TIME_CONFLICT` frontend показує conflict entity/time, якщо дозволено.

## 14. SSE / realtime notifications

Server notification не є consistency mechanism.

SSE може повідомити frontend `entity.updated`, але навіть якщо event затримався/загубився, ETag + transaction + DB constraints гарантують правильність command.

## 15. Acceptance scenarios

Обов'язкові tests:

- 20 concurrent conflicting vehicle assignments → max 1 success;
- 20 conflicting driver assignments → max 1 success;
- two authorize requests → one authorization record;
- same idempotency key same payload → same logical result;
- same key different payload → conflict;
- stale If-Match → no overwrite;
- concurrent waybill creation → unique number;
- retry after simulated deadlock → no duplicate audit/outbox/document.