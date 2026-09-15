# Production Deployment — практичні профілі

Статус: **architecture-v1.6 baseline**

Канонічна мова документа — українська.

## 1. Основний принцип
TransportERP-UA має запускатися від найпростішого реального сценарію: **один комп’ютер, один встановлюваний застосунок, SQLite, локальні документи**.

Центральний сервер, PostgreSQL, Docker, Redis, S3 та багатовузлова інфраструктура не є умовою production-використання малого АТП.

## 2. Профіль A — Local Desktop

Це повноцінний production-профіль для малого підприємства або автономного локального підрозділу.

```text
+--------------------------------------+
| Комп’ютер користувача                |
|--------------------------------------|
| TransportERP-UA desktop application  |
| local backend                        |
| SQLite                               |
| managed documents directory          |
| backup/restore                       |
| transfer/sync client                 |
+--------------------------------------+
```

Користувач:

1. встановлює TransportERP-UA;
2. запускає програму з ярлика;
3. працює у вікні застосунку;
4. не запускає PostgreSQL/Docker вручну;
5. не відкриває `localhost` у браузері;
6. налаштовує каталог резервних копій через сам застосунок.

Внутрішні backend/WebView/service processes запускаються та зупиняються самим застосунком.

## 3. Локальні файли

SQLite DB та документи зберігаються у керованих застосунком каталогах ОС.

Не використовувати поточний робочий каталог програми або випадкові шляхи.

Застосунок повинен мати:

- визначений application data directory;
- окремий documents directory;
- окремий backup destination;
- кнопку/екран відкриття місця зберігання для адміністратора;
- перевірку вільного місця;
- safe shutdown перед технічними операціями з БД.

## 4. Backup Local Desktop

Мінімально підтримуються:

- ручний backup кнопкою;
- автоматичний backup за простим розкладом;
- вибір каталогу, зовнішнього USB-диска або NAS;
- backup SQLite через безпечний backup mechanism, а не копіювання відкритого файла навмання;
- включення документів/вкладень;
- перевірка backup manifest/checksum;
- restore через сам застосунок.

Для малого АТП backup на зовнішній диск є нормальним підтримуваним сценарієм.

## 5. Профіль B — Local + Central

Якщо підприємству потрібен вищий рівень:

```text
Local TransportERP-UA
SQLite
   |
   | оператор підтвердив передачу
   v
Central TransportERP-UA
PostgreSQL
```

Центральний рівень не потрібен для продовження локальної роботи з даними, які ще не передані.

Після central ACK передані дані локально стають read-only.

## 6. Кілька локальних вузлів

Велике підприємство може мати кілька локальних вузлів:

```text
Local A (SQLite) --\
Local B (SQLite) ----> Central (PostgreSQL)
Local C (SQLite) --/
```

Кожний локальний вузол залишається тим самим застосунком. Не потрібна окрема edition або інша локальна БД.

## 7. Центральний рівень

Центральний deployment може бути простим або розділеним залежно від фактичного навантаження.

Початково допустимо:

```text
Central server
- API
- PostgreSQL
- documents storage
- backup
```

Лише коли є реальна потреба, компоненти розносяться на окремі вузли.

Kubernetes не є milestone і не потрібен без доведеної потреби.

## 8. PostgreSQL

PostgreSQL є серверною/центральною технологією, а не локальною обов’язковою залежністю.

На центральному рівні застосовуються:

- server-side transactions;
- FK/UNIQUE/CHECK;
- RLS де воно реально потрібне;
- exclusion constraints;
- row locks;
- server backup tooling.

## 9. Redis

Redis не є обов’язковим компонентом.

Його можна додати центральному deployment лише для конкретної потреби: cache, queue або rate limiting.

## 10. Object storage

S3-compatible storage не є обов’язковим.

Local Desktop використовує файловий каталог.

Central може почати зі звичайного керованого server filesystem і перейти на S3-compatible storage, якщо обсяг/надійність/масштаб це виправдають.

Бізнес-код працює через абстракцію file storage, а не напряму залежить від S3.

## 11. Desktop packaging

Local Desktop повинен постачатися як інсталятор/пакет застосунку.

Вимоги до пакета:

- один зрозумілий installer;
- створення ярлика;
- автоматичне створення application-data каталогів;
- автоматична ініціалізація SQLite;
- schema migration при оновленні;
- rollback/recovery strategy для невдалого оновлення;
- version/build information у UI;
- uninstall не повинен мовчки видаляти production data.

Конкретний desktop shell/package technology перевіряється implementation spike; користувацька модель від неї не залежить.

## 12. Оновлення локального застосунку

Перед schema-changing update:

1. створити локальний recovery backup;
2. закрити write operations;
3. встановити нову версію;
4. виконати SQLite migration;
5. перевірити schema/application startup;
6. лише після успіху відкрити normal mode.

Автооновлення не повинно непомітно ризикувати робочою БД.

## 13. Мережа

Local Desktop без central може працювати без Internet.

Для передачі на central потрібен лише outbound connection до визначеного HTTPS endpoint.

Не потрібно відкривати SQLite file або DB port у мережу.

## 14. Production readiness для Local Desktop

Локальний вузол готовий до production, якщо перевірені:

- clean install;
- first-run DB initialization;
- звичайний restart;
- OS restart;
- backup;
- restore;
- application update + DB migration;
- робота без Internet;
- відновлення після невдалої передачі;
- блокування редагування після central ACK;
- достатньо місця на диску.

## 15. Production readiness для Central

Додатково перевіряються:

- PostgreSQL backup/restore;
- HTTPS;
- central storage backup;
- приймання transfer batches;
- idempotent ACK;
- повернення центральних read-only updates локальним вузлам;
- monitoring відповідно до реального масштабу.

## 16. Принцип масштабування

Спочатку — найпростіша конфігурація, яка надійно виконує роботу.

Ускладнення інфраструктури дозволяється лише при конкретній причині: кількість користувачів, обсяг даних, performance, availability або централізація.
