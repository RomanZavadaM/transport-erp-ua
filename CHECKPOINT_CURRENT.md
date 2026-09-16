# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r6**.
- Working branch: `work/v0.2-python-preview-r6`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r6.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r6_START.zip`.
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
- trips, duties, vehicle/driver assignment and overlap protection;
- medical/technical/dispatcher release controls and final line release;
- waybill creation/list/detail;
- full two-page Taxo 1-АП vector PDF renderer;
- factual departure/return, odometer, mileage and fuel on a waybill;
- close waybill → duty/trips completed and odometer history updated;
- structured fuel history per vehicle created from closed waybills when fuel values are present;
- vehicle card shows fuel history by waybill;
- `PDF 1-АП` uses the current factual-data endpoint while preserving the Taxo renderer;
- persistent PDFs remain outside extracted version folders.

## Taxo / TransportERP boundary

- **Taxo** remains the specialised driver-worktime subsystem: tachograph/tachocard reading, work/driving/rest analysis, Regulation №340 checks, shift schedules, timesheets and activity attestations.
- **TransportERP-UA** owns fleet operations and technical/document workflow: fleet, routes/trips/duties, release, waybills, mileage, fuel, maintenance, repairs and fleet documentation.
- Do not duplicate Taxo tachograph/worktime functionality in TransportERP.

## Packaging rule

Every START ZIP has a unique version/revision in both the ZIP filename and its root folder. Business SQLite databases are never included in START or executable distributions.

## Verified build

GitHub Actions run `35142672048` passed backend lint/typecheck/tests, frontend lint/typecheck/build and START package creation for r6.

## Next step

Primary development direction from r7: **technical fleet management / STOIR**.

1. one odometer history remains the source for all maintenance mileage;
2. vehicle maintenance plan with TO-1 / TO-2 / seasonal / quarterly technical inspection / custom items;
3. due / soon / overdue indicators by mileage and date;
4. maintenance execution history and technical inspection history;
5. technical documentation and journals required by the enterprise workflow;
6. later: defects, repair orders, spare parts and service-provider documents.
