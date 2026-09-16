# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r7**.
- Working branch: `work/v0.2-python-preview-r7`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r7.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r7_START.zip`.
- Daily development launch: `START_WINDOWS.bat` in a per-version Python `.venv`.
- Windows EXE remains a periodic control build only, normally every 5–10 working revisions or at a stable milestone.

## Persistent local data

All preview revisions use one persistent Windows data directory outside version folders:

`%LOCALAPPDATA%\TransportERP-UA`

The SQLite database is `%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`. Documents and backups live under the same persistent data directory. Changing, replacing or deleting an extracted program version must not delete business data.

Use `OPEN_DATA_FOLDER.bat` to open the persistent data directory.

## Current visible functionality

Previous operational functionality remains, plus the first practical STOIR block:

- one vehicle odometer history is the source for maintenance mileage;
- separate STOIR screen linked from the vehicle card;
- maintenance / inspection / OTK / custom plans;
- intervals by kilometres and/or months;
- regulation source: manufacturer / normative / enterprise / custom;
- last completed date and odometer baseline;
- calculated next due date and odometer;
- indicators `OK / DUE_SOON / OVERDUE / NEEDS_BASELINE`;
- configurable warning distance and warning days;
- maintenance/inspection completion record;
- provider / performer / document number / document validity / comment;
- history of completed technical maintenance and inspections;
- completion automatically advances the next due date/odometer.

## Technical direction

TransportERP-UA owns fleet technical management: STOIR, defects, maintenance, repairs, spare parts, technical documents and journals. Taxo remains responsible for driver worktime/tachograph functions.

## Packaging rule

Every START ZIP has a unique version/revision in both the ZIP filename and its root folder. Business SQLite databases are never included in START or executable distributions.

## Verified build

GitHub Actions run `35143435449` passed backend lint/typecheck/tests, frontend lint/typecheck/build and START package creation for r7.

## Next step

Continue practical technical fleet workflow:

`дефект → рішення/блокування експлуатації → ремонтний наряд → роботи/запчастини → виконання → перевірка → закриття ремонту → історія автобуса`.

Then add the technical journals and quarterly inspection planning/printing around the same data, not as duplicate registries.
