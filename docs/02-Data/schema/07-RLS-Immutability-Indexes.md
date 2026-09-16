# Database Integrity — Local SQLite + Central PostgreSQL

Статус: **architecture-v1.6 baseline**

Назва файла історична. RLS є PostgreSQL-specific механізмом central profile і не є вимогою Local Desktop.

## 1. Спільний принцип

Бізнес-правило не повинно існувати тільки у PostgreSQL constraint, якщо те саме правило потрібне Local Desktop.

Канонічний рівень перевірки:

1. application/backend transaction;
2. portable DB constraints, де можливо;
3. DB-specific defense-in-depth додатково.

## 2. Local SQLite

Local використовує:

- transactions;
- `PRAGMA foreign_keys = ON`;
- FK;
- UNIQUE;
- CHECK;
- indexes;
- partial indexes, де підтримуються і виправдані;
- triggers лише для фундаментальних гарантій;
- `row_version` / optimistic locking;
- controlled write transaction для критичних команд.

SQLite file не відкривається напряму іншим робочим місцям через network share. Усі зміни проходять через local backend.

## 3. Central PostgreSQL

Central може додатково використовувати:

- RLS;
- tenant/company context;
- composite tenant-aware FK;
- range types;
- GiST exclusion constraints;
- row locks;
- `FOR UPDATE SKIP LOCKED` для server workers;
- partitioning;
- specialized DB roles.

Ці механізми не повинні ставати вимогою локальної інсталяції.

## 4. Company scope

`company_id` зберігається у business model там, де він потрібен для ідентифікації підприємства/центральної консолідації.

На local node зазвичай працює один enterprise context. Не потрібно емулювати PostgreSQL RLS усередині SQLite.

Central PostgreSQL може застосовувати RLS для ізоляції даних різних company contexts, якщо центральний deployment реально їх містить.

## 5. Authority/read-only invariant

Найважливіший новий invariant v1.6:

- `LOCAL` record може змінювати local backend;
- `CENTRAL` record local backend змінювати не може.

Перевірка виконується кожною mutation command до business write.

Для критичних таблиць SQLite trigger може додатково блокувати direct update/delete `CENTRAL` rows як defense-in-depth.

Migration/recovery tooling працює через окремий контрольований режим.

## 6. Transfer invariants

Обов’язково:

- batch не переходить у `TRANSFERRING` без local approval;
- approved payload не змінюється без повторного approval;
- authority не переходить у `CENTRAL` до valid central ACK;
- retry тієї самої передачі не створює дублікати на central;
- central update, повернений local, не повертає authority назад у `LOCAL`.

## 7. Immutable history

Залишаються append-only/immutable принципи для:

- audit;
- trip/duty operational events, де застосовуються;
- closed snapshots;
- finalized Waybill version content;
- completed control evidence;
- correction evidence.

Local SQLite та central PostgreSQL повинні забезпечувати однакову business semantics, навіть якщо physical constraints різні.

## 8. Completed checks

Completed medical/technical check не редагується напряму.

Виправлення = invalidation/correction + new record.

Це application rule; SQLite trigger може його підсилити.

## 9. Closed aggregates

Після terminal/closed state historical core fields не UPDATE-яться звичайною mutation command.

Correction створює нову version/snapshot і змінює effective pointer за контрольованою процедурою.

## 10. Resource conflict rules

Один driver/vehicle не може бути призначений на несумісні одночасні роботи.

### Local SQLite

Критична command виконується в контрольованій write transaction:

1. почати write transaction;
2. перечитати актуальні assignments;
3. перевірити overlap;
4. записати assignment;
5. commit.

Оскільки local database writer координується одним backend application, не будуємо PostgreSQL-like distributed locking усередині desktop.

### Central PostgreSQL

Додатково може використовувати GiST exclusion constraint/locking як defense-in-depth.

## 11. Indexes Local

Додаємо лише indexes під реальні operational queries.

Початково потрібні:

- users status/username;
- vehicles status/depot;
- drivers status/depot;
- trips service date/status;
- duties service date/status;
- active assignments by vehicle/driver/time;
- Waybill number/status;
- transfer batch status/time;
- transfer items entity id;
- audit entity/time;
- document validity dates.

Не створюємо GIN/JSON indexes “про всяк випадок”.

## 12. Indexes Central

Central додає ті самі operational indexes плюс спеціалізовані PostgreSQL indexes після profiling.

`pg_stat_statements`/`EXPLAIN` застосовуються central, а не є local prerequisite.

## 13. Audit partitioning

Local audit починається **unpartitioned**.

Central partitioning вводиться лише коли обсяг даних/retention operations це виправдовують.

Architecture-v1.6 не вимагає monthly partitions від першого дня.

## 14. DB roles

### Local SQLite

Немає окремих PostgreSQL DB roles. Захист від звичайного користувацького редагування забезпечує application packaging, filesystem permissions, backend rules, backup та audit.

### Central PostgreSQL

Можуть бути:

- migration role;
- runtime role;
- reporting role;
- backup role.

## 15. Migration CI

CI має тестувати обидва physical profiles:

### SQLite

- clean install;
- migration upgrade;
- FK enabled;
- critical constraints/triggers;
- local authority blocking;
- backup/restore fixture;
- interrupted transfer recovery.

### PostgreSQL central

- clean install/upgrade;
- server constraints;
- RLS, якщо воно ввімкнене;
- central receive idempotency;
- ACK receipt integrity.

## 16. Практичне правило

Якщо нова функція працює лише тому, що PostgreSQL має специфічний feature, потрібно перевірити, як те саме business rule працює на Local SQLite, перш ніж приймати дизайн.
