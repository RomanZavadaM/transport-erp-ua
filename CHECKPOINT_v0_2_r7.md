# TransportERP-UA — CHECKPOINT v0.2 TEST r7

Date: 2026-09-16

## Scope

First practical STOIR / technical fleet checkpoint.

## Implemented

- separate STOIR screen for each vehicle;
- STOIR access from the vehicle card;
- one shared odometer history remains the source of maintenance mileage;
- maintenance plans for `MAINTENANCE`, `INSPECTION`, `OTK`, `CUSTOM`;
- plan basis source: `MANUFACTURER`, `NORMATIVE`, `ENTERPRISE`, `CUSTOM`;
- intervals by kilometres and/or months;
- baseline from last completed date/odometer;
- calculated next due date and next due odometer;
- remaining kilometres/days;
- practical status indicators: `NEEDS_BASELINE`, `OK`, `DUE_SOON`, `OVERDUE`;
- configurable warning thresholds;
- maintenance/inspection completion;
- performer/provider/document number/document validity/comment;
- completed STOIR event history;
- successful completion updates the plan baseline and next due values.

## Data persistence

All data remain in the common local SQLite database under `%LOCALAPPDATA%\TransportERP-UA`, outside extracted test-version folders. r7 does not include a database inside its START ZIP.

## Verification

GitHub Actions run `35143435449` passed backend lint/typecheck/tests, frontend lint/typecheck/build and START package creation.

## Next

r8: defects and repair workflow:

`дефект → блокування експлуатації за потреби → ремонтний наряд → роботи/запчастини → виконання/перевірка → закриття → технічна історія автобуса`.
