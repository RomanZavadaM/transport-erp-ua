# TransportERP-UA — CHECKPOINT v0.2 TEST r4

Date: 2026-09-16

## Version

- Version: **v0.2 TEST r4**.
- Branch: `work/v0.2-python-preview-r4`.
- Manual-test package: `TransportERP-UA_v0.2_TEST_r4_START.zip`.
- Launch: `START_WINDOWS.bat` → per-version `.venv` → local desktop application.

## What changed since r3

### Waybill workflow

- Added waybill candidates from already released duties.
- A waybill cannot be created before final line release.
- One duty can have only one waybill.
- Waybill number is unique within the local company scope.
- Added waybill list and detail screens.

### Taxo 1-АП document

The TransportERP renderer now uses the full Taxo two-page vector implementation of the user's 1-АП waybill scan as the rendering baseline rather than a simplified HTML imitation.

- A4 landscape, two pages.
- Page 1: enterprise/waybill header, vehicle, driver, planned departure/return, control blocks, route/work accounting, mileage/trips/fuel tables and signatures.
- Page 2: outbound/return route tables, doctor, odometer, mechanic and road-control blocks.
- Known TransportERP values are filled automatically; fields not yet captured by ERP remain blank for later/factual entry.
- `PDF 1-АП` is available from the waybill list.
- Generated PDFs are stored under the persistent TransportERP documents directory, outside extracted version folders.

### Project boundary with Taxo

- Taxo remains focused on driver working-time/tachograph functions: tachocard reading, work/driving/rest analysis, Regulation №340, shift schedules, timesheets and activity attestations.
- TransportERP owns fleet and technical/document workflows: fleet, routes/trips/duties, line release, waybills, mileage, fuel, maintenance, repairs and technical documentation.
- TransportERP must not duplicate Taxo-owned tachograph/worktime features.
- Data identifiers/integration points are kept suitable for future connection between the two projects.

## Persistent data

The database remains outside the version package:

`%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`

Documents and backups are also outside version folders. Moving from r3 to r4 does not reset business data.

## Verification

GitHub Actions run `35140672263` completed successfully:

- backend lint/typecheck/tests;
- Taxo-style PDF generation test;
- frontend lint/typecheck/build;
- versioned START folder;
- START ZIP artifact.

## Next development target

Complete the factual return/closing workflow:

1. actual departure;
2. actual return;
3. odometer start/end and calculated mileage;
4. fuel issue/return/consumption fields;
5. close the waybill only when required factual values are present;
6. regenerate/store the final PDF revision.
