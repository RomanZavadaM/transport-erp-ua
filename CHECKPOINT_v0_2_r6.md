# TransportERP-UA — CHECKPOINT v0.2 TEST r6

Date: 2026-09-16

## Version

- Version: **v0.2 TEST r6**.
- Branch: `work/v0.2-python-preview-r6`.
- Manual-test package: `TransportERP-UA_v0.2_TEST_r6_START.zip`.
- Launch: `START_WINDOWS.bat` → per-version `.venv` → local desktop application.

## What changed since r5

### Fuel history

- Closed waybills with complete fuel values now create one structured vehicle fuel-history record.
- Stored values: service date, waybill, driver, fuel at departure, issued fuel, fuel at return and calculated consumption.
- Closing a waybill without fuel values does not create a fake fuel record.
- Vehicle card shows `Паливо за шляхівками` and links entries back to the waybill.

### Current factual 1-АП PDF path

- Added a factual PDF endpoint that enriches the existing Taxo renderer data with actual departure/return, odometer and calculated mileage/fuel values when present.
- Waybill list `PDF 1-АП` action uses the current factual-data endpoint.
- Taxo renderer geometry remains isolated and unchanged as the rendering baseline.

## Persistent data

SQLite remains outside the program version:

`%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`

Version replacement does not remove fuel history, waybills, odometer data or documents.

## Verification

GitHub Actions run `35142672048` completed successfully:

- backend lint/typecheck/tests;
- fuel history tests including no-fake-record case;
- frontend lint/typecheck/build;
- versioned r6 START folder and ZIP.

## Next development direction

From r7 the main work moves to the technical side of the fleet:

- STOIR maintenance plans;
- mileage/date-driven TO planning;
- quarterly passenger-vehicle technical inspections;
- technical maintenance/inspection history;
- technical documents and electronic journals;
- later defects, repair orders, spare parts and external service documents.
