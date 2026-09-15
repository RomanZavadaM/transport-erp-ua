# Local Desktop Application — practical profile

Статус: **architecture-v1.6 implementation baseline / M1.5 spike target**

## 1. Що отримує користувач

Користувач встановлює **TransportERP-UA** як звичайну програму.

Після встановлення:

- є ярлик у меню/на робочому столі;
- запуск відкриває одне вікно TransportERP-UA;
- не відкривається браузерна вкладка;
- не потрібно запускати `python`, `uvicorn`, Docker або PostgreSQL;
- при першому запуску програма сама створює локальну SQLite БД і службові каталоги.

## 2. Внутрішня схема процесів

```text
TransportERP-UA desktop shell
        |
        +-- запускає local backend
        |       |
        |       +-- SQLite
        |       +-- documents
        |       +-- backup/transfer services
        |
        +-- показує UI у embedded WebView
```

Backend bind-иться тільки на loopback (`127.0.0.1`) у Local Desktop profile.

Користувач не працює з URL/портом напряму.

## 3. Перший packaging spike

Першим перевіряємо **pywebview + packaged Python backend** як найпростіший шлях для наявного FastAPI/Python стеку.

Причини:

- не потребує Electron/Chromium bundle;
- не додає Rust-sidecar architecture до першого desktop prototype;
- може використовувати системний WebView;
- Python application/backend можна збирати в один керований desktop package;
- однакова концепція можлива для Windows/macOS/Linux.

Це не незмінний ADR про бібліотеку. Spike повинен довести інсталяцію, запуск, shutdown, update і recovery. Якщо pywebview дає неприйнятні проблеми, наступний кандидат — Tauri shell + packaged Python sidecar.

## 4. Windows — перша практична ціль

Перший acceptance target — звичайний Windows 10/11 x64 ПК без встановленого PostgreSQL/Python/Docker.

Installer повинен:

1. встановити program binaries;
2. створити application-data directory;
3. створити/перевірити permissions для data directory;
4. створити ярлик;
5. перевірити/забезпечити WebView runtime requirement, якщо desktop shell його потребує;
6. **не видаляти production data під час звичайного uninstall без окремого явного рішення користувача**.

## 5. Program files ≠ business data

Program binaries і business data зберігаються окремо.

Windows baseline:

```text
Program Files\TransportERP-UA\        program binaries
ProgramData\TransportERP-UA\          business/application data
  data\transporterp.db                 SQLite
  documents\                           PDF/attachments
  logs\                                rotating logs
  state\                               node/version/technical state
```

Backup destination **не** повинен за замовчуванням бути тим самим physical disk як єдина резервна копія.

Конкретні OS paths оформлюються через один platform-path service; business code не hardcode-ить Windows paths.

## 6. Single instance

Local data directory обслуговує один backend process.

При запуску:

- application бере instance/data lock;
- якщо backend уже працює, другий launcher або активує існуюче вікно, або показує зрозуміле повідомлення;
- не запускаються два незалежні writers до того самого SQLite file.

## 7. Startup sequence

1. locate/create application data directory;
2. acquire single-instance lock;
3. open logs;
4. verify free disk space;
5. open SQLite;
6. set/verify required SQLite pragmas;
7. verify schema version;
8. run pending safe migrations if allowed by update workflow;
9. start local backend on loopback;
10. wait internal health check;
11. open desktop WebView window;
12. show recovery screen instead of blank window if startup failed.

## 8. Shutdown sequence

1. desktop shell requests graceful backend shutdown;
2. new writes stop;
3. active local transaction finishes/rolls back;
4. delivery worker stops cleanly;
5. DB connections close;
6. process exits;
7. force-kill only as fallback.

Network transfer must never require keeping an SQLite write transaction open while waiting for central.

## 9. SQLite baseline

Required at startup:

- foreign keys enabled;
- tested journal/synchronous policy;
- busy timeout policy;
- integrity/recovery behavior tested after forced application termination.

SQLite file is never a supported multi-PC network-share database.

## 10. Files

Documents live in managed `documents` directory.

DB stores metadata/reference/checksum; large binary documents are not stored blindly inside SQLite unless a specific document type later justifies it.

## 11. Backup UI

Local application has:

- `Створити резервну копію`;
- `Відновити з резервної копії`;
- backup destination selector;
- last backup status;
- automatic schedule toggle/basic schedule;
- warning when backup is overdue or destination unavailable.

Backup package includes SQLite + documents + manifest/version metadata.

## 12. Update

Before schema-changing application update:

1. create automatic recovery backup;
2. verify backup;
3. install new binaries;
4. run local DB migration;
5. verify startup/integrity;
6. mark update successful.

If migration/startup fails, application must enter recovery mode rather than repeatedly damaging the same DB.

## 13. Transfer UI

Operator sees a normal business screen, not queue internals.

Minimum:

- `Підготовано до передачі`;
- what records/package are included;
- who/what initiated preparation: manual / request from central / rule;
- `Підтвердити передачу`;
- `Відхилити/скасувати` where allowed;
- current delivery status;
- clear error/retry state;
- clear label when record is already managed centrally/read-only.

Central request or rule never clicks `Підтвердити` on behalf of local operator.

## 14. Local authority behavior

- authority=`LOCAL`: normal local edits allowed if business state permits and no active transfer lock;
- approved active transfer: authority still `LOCAL`, but approved records temporarily transfer-locked;
- valid central ACK: authority becomes `CENTRAL`, local business edit permanently disabled;
- central-returned newer version updates local read-only copy.

## 15. Offline behavior

Without Internet/central:

- desktop application starts normally;
- local business workflow works;
- backup works;
- prepared transfer stays pending;
- approved failed transfer shows error/retry state;
- no record becomes `CENTRAL` without ACK.

## 16. M1.5 desktop acceptance test

On a clean Windows PC/VM:

1. install from one installer;
2. launch from shortcut;
3. no browser opens;
4. no PostgreSQL/Python/Docker prerequisite installation by user;
5. create local data;
6. close and reopen application;
7. reboot Windows and reopen;
8. work with network disabled;
9. create backup to second path/device;
10. restore into clean test data directory;
11. prepare transfer by rule/central request;
12. verify operator confirmation is still required;
13. interrupt transfer;
14. verify authority stays `LOCAL`;
15. retry and receive ACK;
16. verify local record becomes read-only;
17. uninstall/reinstall application without silently deleting business data.

M1.5 desktop foundation is not accepted until this scenario passes.
