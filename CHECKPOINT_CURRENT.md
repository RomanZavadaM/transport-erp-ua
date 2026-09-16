# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r4**.
- Working branch: `work/v0.2-python-preview-r4`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r4.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r4_START.zip`.
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
- **full two-page Taxo 1-АП vector PDF renderer** adapted to TransportERP data;
- `PDF 1-АП` action from the waybill list;
- generated PDFs stored outside the program version under the persistent documents directory.

## Taxo / TransportERP boundary

- **Taxo** remains the specialised driver-worktime subsystem: tachograph/tachocard reading, work/driving/rest analysis, Regulation №340 checks, shift schedules, timesheets and activity attestations.
- **TransportERP-UA** owns fleet operations and technical/document workflow: fleet, routes/trips/duties, release, waybills, mileage, fuel, maintenance, repairs and fleet documentation.
- Do not duplicate Taxo tachograph/worktime functionality in TransportERP. Keep driver/vehicle/route/date/duty/trip identifiers and integration points compatible for future connection.

## Packaging rule

Every START ZIP has a unique version/revision in both the ZIP filename and its root folder. Business SQLite databases are never included in START or executable distributions.

## Verified build

GitHub Actions run `35140672263` passed backend tests, frontend lint/typecheck/build, Taxo-style waybill PDF generation and START package creation.

## Next step

Continue with the practical completion of the trip document workflow:

`фактичний виїзд → фактичне повернення → одометр/пробіг → паливо → закриття шляхівки`.

Do not expand Taxo-owned worktime/tachograph functionality inside TransportERP.
