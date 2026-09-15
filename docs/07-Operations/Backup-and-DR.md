# Резервне копіювання та відновлення

Статус: **architecture-v1.6 baseline**

## 1. Мета
Backup повинен дозволяти реально відновити робочий TransportERP-UA після поломки комп’ютера, диска, помилки оновлення або втрати центрального сервера.

Політика розділяється на:

1. Local Desktop;
2. Central server.

Для малого АТП не вимагається серверна backup-інфраструктура.

## 2. Local Desktop — що резервуємо

Обов’язково:

- SQLite operational database;
- документи/PDF/вкладення;
- локальні налаштування, необхідні для відновлення;
- transfer state/receipts;
- application/schema version metadata.

Не потрібно резервувати перевстановлювані program binaries як єдину копію — їх можна відновити з release package.

## 3. Local Desktop — практичний механізм

Backup запускається самим застосунком.

Підтримуються:

- `Створити резервну копію зараз`;
- простий автоматичний розклад;
- вибір каталогу;
- зовнішній USB-диск;
- NAS/network share;
- за потреби синхронізований cloud folder, якщо це дозволено політикою підприємства.

SQLite копіюється через штатний consistent backup mechanism/application transaction, а не простим копіюванням відкритого DB-файла.

Пакет backup містить manifest з:

- датою/часом;
- application version;
- schema version;
- node id;
- DB checksum;
- переліком/контролем документів.

## 4. Просте правило для малого АТП

Мінімальний прийнятний варіант:

- робочі дані на локальному диску;
- автоматична копія на інший фізичний носій або NAS;
- періодична перевірка restore.

Другий каталог того самого фізичного диска не захищає від поломки диска.

## 5. Restore Local Desktop

Restore виконується з UI застосунку або recovery mode.

Послідовність:

1. вибрати backup package;
2. перевірити manifest/checksum;
3. створити safety copy поточного стану, якщо він існує;
4. закрити normal write mode;
5. відновити SQLite та документи;
6. перевірити schema/version;
7. запустити integrity checks;
8. відкрити normal mode.

Користувач малого АТП не повинен вручну виконувати SQL-команди.

## 6. Backup перед оновленням

Перед локальним оновленням, яке змінює схему БД, застосунок автоматично створює recovery backup.

Якщо backup створити не вдалося, небезпечне schema update не починається без явного адміністративного рішення.

## 7. Передані в центр дані

Central ACK не заміняє локальний backup.

Локальна read-only копія переданих даних зберігається та входить у backup відповідно до retention policy.

Central також має власний backup.

## 8. Central server

Для центрального рівня з PostgreSQL використовуються звичайні server-grade механізми:

- PostgreSQL backup tooling;
- за потреби WAL/PITR;
- backup server documents/object storage;
- off-site copy;
- restore verification.

Конкретні RPO/RTO визначаються масштабом підприємства і не нав’язуються малому Local Desktop deployment.

## 9. Central PostgreSQL backup

Для значущого production central рекомендуються `pgBackRest`, `WAL-G` або еквівалентне перевірене рішення.

Можливі:

- regular full/incremental backup;
- WAL archiving/PITR;
- encrypted off-site repository;
- automated verification.

Це вимога центрального серверного профілю, а не локального desktop.

## 10. Файли

Local Desktop використовує filesystem managed application directory.

Central може використовувати filesystem, NAS або S3-compatible storage залежно від масштабу.

Для важливих immutable документів бажано зберігати SHA-256 у БД незалежно від фізичного storage backend.

## 11. Перевірка відновлення

Backup не вважається достатнім, якщо жодного разу не перевірено restore.

Для малого вузла достатній простий контрольований тест відновлення на резервний каталог/тестову копію.

Для central server restore drills мають бути регулярнішими та формалізованими відповідно до ризику.

## 12. Аварійні сценарії Local Desktop

### LD-01 — зламався застосунок, дані цілі
Перевстановити application package, підключити/знайти application data, перевірити DB migration/version.

### LD-02 — зламався диск/комп’ютер
Встановити TransportERP-UA на replacement PC → `Відновити з резервної копії` → перевірити integrity → продовжити роботу.

### LD-03 — невдале оновлення
Запустити recovery mode → відновити automatic pre-update backup → повернути сумісну application version.

### LD-04 — пошкоджена SQLite
Не редагувати DB вручну як перший крок. Зупинити normal writes, зробити forensic/safety copy, перевірити SQLite integrity, за потреби відновити останній valid backup.

### LD-05 — central недоступний
Локальна робота з даними у стані `LOCAL` продовжується. Pending transfers залишаються pending; дані не блокуються без ACK.

## 13. Аварійні сценарії Central

Central outage не повинен робити Local Desktop непрацездатним для локально authoritative даних.

Після відновлення central transfer client продовжує підтверджені, але не завершені передачі idempotently.

## 14. Production readiness

### Local Desktop
Перед запуском перевірити:

- backup кнопкою;
- scheduled backup;
- restore;
- backup на інший носій;
- pre-update backup;
- recovery після OS restart;
- recovery після interrupted transfer.

### Central
Додатково:

- PostgreSQL backup/restore;
- server storage restore;
- off-site copy;
- transfer receipt/ACK recovery;
- monitoring backup failures.
