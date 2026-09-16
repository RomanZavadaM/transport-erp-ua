# TransportERP-UA — CHECKPOINT v0.2 TEST r2

Date: 2026-09-16

## Version

- Version: **v0.2 TEST r2**.
- Working branch: `work/v0.2-python-preview-r2`.
- Manual-test package: `TransportERP-UA_v0.2_TEST_r2_START.zip`.
- Launch: `START_WINDOWS.bat` in a per-version Python `.venv`.

## Persistent local data

Runtime data are stored outside every version folder so test upgrades do not lose data:

- Windows data directory: `%LOCALAPPDATA%\TransportERP-UA`
- SQLite database: `%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`
- documents: `%LOCALAPPDATA%\TransportERP-UA\documents`
- backups: `%LOCALAPPDATA%\TransportERP-UA\backups`

`OPEN_DATA_FOLDER.bat` opens the persistent data directory. START packages reject bundled `.db`, `.sqlite` and `.sqlite3` files.

An automated test verifies that two different extracted version folders resolve to the same Windows database path.

## Visible functionality in r2

Everything from r1 plus the first operational dispatch workflow:

- schedules: route + departure time + arrival time;
- choose an operational date;
- generate planned trips for that date from the schedule;
- select one or more non-overlapping trips;
- assign an active vehicle and active driver;
- create a duty (наряд) containing 1..N trips;
- list duties for the selected date;
- show assigned duty on each trip;
- prevent the same vehicle from being assigned to overlapping trips;
- prevent the same driver from being assigned to overlapping trips.

The home screen now exposes the **«Наряди і рейси»** module.

## Automated verification

The Windows START workflow is green for the r2 implementation:

- backend Ruff;
- backend mypy;
- backend pytest including operations and persistent-data tests;
- frontend ESLint;
- frontend TypeScript;
- frontend static build;
- versioned START folder creation;
- no database files bundled;
- START ZIP upload.

## Next manual test

Use real r1 data, extract r2 to a new folder and launch `START_WINDOWS.bat`. Existing vehicles, drivers and routes should remain visible because both revisions use the same external SQLite database. Then test the new `Наряди і рейси` screen.
