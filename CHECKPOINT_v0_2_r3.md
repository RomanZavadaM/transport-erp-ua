# TransportERP-UA — CHECKPOINT v0.2 TEST r3

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r3**.
- Working branch: `work/v0.2-python-preview-r3`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r3_START.zip`.
- Launch: `START_WINDOWS.bat` in a per-version Python `.venv`.
- Windows EXE remains a periodic control build only, normally every 5–10 working revisions or at a stable milestone.

## Persistent local data

All revisions use the same data directory outside extracted program folders:

`%LOCALAPPDATA%\TransportERP-UA`

Main SQLite database:

`%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`

Changing from r1/r2 to r3 does not replace or delete business data. New local functionality adds its own tables to the existing SQLite database when first used.

## Added in r3

### Line release workflow

- new visible module `Випуск на лінію`;
- list of duties for a selected work date;
- medical control: `Допущено / Не допущено` + person who performed the check;
- technical control: `Допущено / Не допущено` + mechanic;
- dispatcher decision: `Дозволено / Заборонено` + dispatcher;
- final `Випустити на лінію` action;
- release is blocked until medical = PASSED, technical = PASSED, dispatcher = APPROVED;
- after final release, the local control record is locked against ordinary edits;
- released duty remains visible with a clear released state.

## Tests

Automated tests cover:

- release rejection without positive medical control;
- release rejection without positive technical control;
- release rejection without dispatcher approval;
- successful release after all three positive controls;
- failed control blocks release;
- control editing is blocked after release;
- release list returns duties for the selected date;
- existing r2 operations, local SQLite, backup and frontend builds remain green.

## Packaging and data rules

- every START ZIP has a unique version/revision in both filename and root folder;
- no `.db`, `.sqlite` or `.sqlite3` file is included in the program archive;
- use `OPEN_DATA_FOLDER.bat` to open the persistent data location;
- each revision gets its own `.venv`, while business data stay common.

## Next practical step

Manually test the full chain:

`Маршрут → розклад → рейси → наряд → медконтроль → техконтроль → дозвіл диспетчера → випуск`.

After UI/workflow corrections, continue with the first practical waybill workflow rather than adding new infrastructure layers.
