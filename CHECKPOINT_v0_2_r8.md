# TransportERP-UA — CHECKPOINT v0.2 TEST r8

Date: 2026-09-16

## Release point

- Version: **v0.2 TEST r8**.
- Release branch: `release/v0.2-r8`.
- Source branch: `work/v0.2-python-preview-r8`.
- Green CI base commit: `c126d2932a416b4d12d0336995e3a6adb4666893`.
- Verified CI run: `35145861554`.
- Release tag: `v0.2-r8`.
- Release type: testing prerelease.

## Visible functionality

- local desktop app with SQLite;
- persistent external business data directory;
- company settings;
- vehicles, vehicle card, documents and odometer history;
- drivers and driver documents;
- stops and routes;
- schedules, dated trips and duties;
- vehicle/driver assignment with overlap checks;
- medical / technical / dispatcher release controls;
- waybill creation after release;
- Taxo-derived two-page 1-AP PDF renderer;
- actual departure/return, odometer, mileage, fuel and waybill closing;
- fuel history per vehicle;
- STOIR plans and completed technical maintenance/inspection history;
- defects and repair orders;
- repair works / parts / materials / cost;
- repair completion and technical close;
- local ZIP backup.

## Data safety

Business data do not live in version folders and must not be bundled into START or executable packages.

Windows persistent root:
`%LOCALAPPDATA%\TransportERP-UA`

macOS persistent root:
`~/Library/Application Support/TransportERP-UA`

## Release assets

Taxo-style publication set:

- `TransportERP-UA_v0_2_TEST_r8_START.zip`
- `TransportERP-UA_v0_2_TEST_r8_Windows_x64_Portable.zip`
- `TransportERP-UA_v0_2_TEST_r8_Setup_Windows_x64.exe`
- `TransportERP-UA_v0_2_TEST_r8_macOS_arm64_Portable.zip`
- `TransportERP-UA_v0_2_TEST_r8_macOS_x86_64_Portable.zip`
- `SHA256SUMS_v0_2_TEST_r8.txt`

## Known testing limitation

The technical module can mark a vehicle as `REPAIR` through blocking defects/repair orders, but the dispatcher release endpoint is not yet hard-blocked by those technical blockers. That connection is planned for r9 and must not be silently treated as implemented in r8.
