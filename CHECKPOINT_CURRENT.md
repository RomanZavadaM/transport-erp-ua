# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r5**.
- Working branch: `work/v0.2-python-preview-r5`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r5.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r5_START.zip`.
- Daily development launch: `START_WINDOWS.bat` in a per-version Python `.venv`.
- Windows EXE remains a periodic control build only, normally every 5–10 working revisions or at a stable milestone.

## Persistent local data

All preview revisions use one persistent Windows data directory outside version folders:

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
- vehicle and driver assignment with overlap protection;
- medical pre-trip control;
- technical pre-trip control;
- dispatcher authorization;
- final line release with locking after release;
- waybill creation only from a released duty;
- unique waybill number and one waybill per duty;
- waybill list/detail screens;
- full two-page Taxo 1-АП vector PDF renderer;
- `PDF 1-АП` action and persistent PDF storage;
- factual departure and return recording;
- odometer at departure/return with calculated mileage;
- fuel at departure / issued / remaining with calculated consumption;
- waybill close command requiring essential factual values;
- closing the waybill completes its duty and trips;
- closed waybill factual data are read-only;
- closing automatically writes departure/return odometer readings into vehicle history.

## Taxo / TransportERP boundary

- **Taxo** remains the specialised driver-worktime subsystem: tachograph/tachocard reading, work/driving/rest analysis, Regulation №340 checks, shift schedules, timesheets and activity attestations.
- **TransportERP-UA** owns fleet operations and technical/document workflow: fleet, routes/trips/duties, release, waybills, mileage, fuel, maintenance, repairs and fleet documentation.
- Do not duplicate Taxo tachograph/worktime functionality in TransportERP. Keep driver/vehicle/route/date/duty/trip integration points compatible for future connection.

## Packaging rule

Every START ZIP has a unique version/revision in both the ZIP filename and its root folder. Business SQLite databases are never included in START or executable distributions.

## Verified build

GitHub Actions run `35141482809` passed backend lint/typecheck/tests, frontend lint/typecheck/build and START package creation for r5.

## Next step

Improve the factual document output and fleet workflow without duplicating Taxo:

1. carry factual odometer/mileage/fuel into the 1-АП PDF;
2. add structured fuel operation history;
3. begin technical maintenance / repair workflow from the vehicle card.
