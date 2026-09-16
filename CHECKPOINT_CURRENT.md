# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current release candidate

- Version: **v0.2 TEST r8**.
- Release branch: `release/v0.2-r8`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r8.md`.
- Release tag: `v0.2-r8`.
- Release type: testing prerelease.
- Green CI base commit: `c126d2932a416b4d12d0336995e3a6adb4666893`.
- Verified CI run: `35145861554`.

## Persistent local data

All preview/executable revisions use one persistent data directory outside version folders.

Windows:
`%LOCALAPPDATA%\TransportERP-UA`

macOS:
`~/Library/Application Support/TransportERP-UA`

The SQLite database, documents and backups remain outside START/Portable/Setup packages. Changing program versions must not delete business data.

## Current visible functionality

- local desktop app with SQLite;
- enterprise settings;
- vehicles, vehicle card, documents and odometer;
- drivers and documents;
- stops and routes;
- schedules, dated trips and duties;
- vehicle/driver assignment with overlap checks;
- medical / technical / dispatcher release controls;
- waybill creation and two-page 1-AP PDF based on the Taxo renderer;
- actual departure/return, odometer, mileage, fuel and waybill closing;
- fuel history per vehicle;
- STOIR plans for maintenance / inspection / OTK / custom work;
- mileage/date due calculations and warnings;
- completed technical maintenance/inspection history;
- technical service screen;
- defects with severity and blocking flag;
- repair orders, works, parts, materials, cost, completion and technical close;
- local ZIP backup.

## Project boundary with Taxo

TransportERP-UA owns fleet operations, technical management, STOIR, repairs, documents, mileage, fuel, release and waybills.

Taxo remains the specialized driver-worktime/tachograph subsystem: tachograph cards, driving/rest, Regulation №340 analysis, shift schedules, timesheets and activity confirmation forms.

## Packaging rule

Release packages follow the Taxo format and always have unique versioned names/root folders. Business SQLite databases are never bundled.

Current release set:

- `TransportERP-UA_v0_2_TEST_r8_START.zip`
- `TransportERP-UA_v0_2_TEST_r8_Windows_x64_Portable.zip`
- `TransportERP-UA_v0_2_TEST_r8_Setup_Windows_x64.exe`
- `TransportERP-UA_v0_2_TEST_r8_macOS_arm64_Portable.zip`
- `TransportERP-UA_v0_2_TEST_r8_macOS_x86_64_Portable.zip`
- `SHA256SUMS_v0_2_TEST_r8.txt`

## Known limitation for r8

Blocking defects/repair orders already move a vehicle into `REPAIR`, but final dispatcher release is not yet hard-blocked by that technical blocker. This is explicitly planned for r9.
