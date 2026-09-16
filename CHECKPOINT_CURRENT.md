# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r2**.
- Working branch: `work/v0.2-python-preview-r2`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r2.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r2_START.zip`.
- Daily development launch: `START_WINDOWS.bat` in a per-version Python `.venv`.
- Windows EXE is a periodic control build only, normally every 5–10 working revisions or at a stable milestone.

## Persistent local data

All preview revisions use one persistent Windows data directory outside the version folders:

`%LOCALAPPDATA%\TransportERP-UA`

The SQLite database is `%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`. Documents and backups live under the same persistent data directory. Changing, replacing or deleting an extracted program version must not delete business data.

Use `OPEN_DATA_FOLDER.bat` to open the persistent data directory.

## Current visible functionality

- enterprise settings;
- vehicles, vehicle cards, documents and odometer;
- drivers and driver documents;
- stops and routes;
- local system status and ZIP backup;
- schedules by route and planned times;
- generation of trips for a selected date;
- duties containing 1..N trips;
- vehicle and driver assignment;
- overlap protection for vehicle and driver assignments.

## Packaging rule

Every START ZIP has a unique version/revision in both the ZIP filename and its root folder. Business SQLite databases are never included in START or executable distributions.

## Next step

Manually test `v0.2 TEST r2 START` against the same persistent data created with r1. Fix practical UI/workflow issues as r3 before expanding into release/medical/technical control.
