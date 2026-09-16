# TransportERP-UA — CHECKPOINT v0.2 TEST r5

Date: 2026-09-16

## Version

- Version: **v0.2 TEST r5**.
- Branch: `work/v0.2-python-preview-r5`.
- Manual-test package: `TransportERP-UA_v0.2_TEST_r5_START.zip`.
- Launch: `START_WINDOWS.bat` → per-version `.venv` → local desktop application.

## What changed since r4

### Factual waybill workflow

Added a practical close-out workflow to the waybill screen:

- factual departure date/time;
- factual return date/time;
- odometer at departure;
- odometer at return;
- calculated mileage;
- fuel at departure;
- fuel issued during the duty;
- fuel remaining on return;
- calculated fuel consumption;
- operator note;
- save factual values while the waybill is open;
- close the waybill only when departure, return and both odometer readings are present.

### Closing behaviour

When the waybill is closed:

- waybill status becomes `CLOSED`;
- its factual values become read-only;
- duty status becomes `COMPLETED`;
- linked trip statuses become `COMPLETED`;
- departure and return odometer readings are added to the vehicle odometer history;
- odometer cannot decrease;
- return cannot be earlier than departure;
- calculated fuel consumption cannot be negative.

Fuel values are optional because not every duty includes a fuel issue operation. When start/issued/end fuel values are all present, actual consumption is calculated automatically.

## Previous r4 functionality retained

- waybill creation only after line release;
- unique waybill number / one waybill per duty;
- full Taxo two-page vector 1-АП renderer;
- persistent generated PDF documents;
- separate persistent SQLite data outside version folders.

## Persistent data

Database:

`%LOCALAPPDATA%\TransportERP-UA\transport-erp.sqlite3`

Changing from r4 to r5 does not reset existing business data. New factual waybill storage is added to the same database on demand.

## Verification

GitHub Actions run `35141482809` completed successfully:

- backend lint/typecheck/tests;
- new factual close-out tests;
- frontend lint/typecheck/build;
- versioned r5 START folder and ZIP.

## Next development target

1. Fill 1-АП PDF with factual odometer/mileage/fuel values.
2. Add structured fuel operation history to the vehicle/waybill workflow.
3. Start technical maintenance / repair functionality in TransportERP, while leaving tachograph/worktime functionality in Taxo.
