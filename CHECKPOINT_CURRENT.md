# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r1**.
- Working branch: `work/v0.2-python-preview-r1`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r1.md`.
- Primary manual-test package: `TransportERP-UA_v0.2_TEST_r1_START.zip`.
- Daily development launch: `START_WINDOWS.bat` in Python `.venv`.
- Windows EXE is a periodic control build only, normally every 5–10 working revisions or at a stable milestone.

## Current practical focus

The application is now tested from real packages before adding large new areas. Current visible modules are enterprise settings, vehicles, vehicle card/documents/odometer, drivers, driver card/documents, stops, routes, system status and local backup.

## Packaging rule

Every ZIP has a unique versioned root folder matching the archive version. Business SQLite databases are never included in source/START or executable distributions.

## Next step

Build and manually test `v0.2 TEST r1 START`, collect UI/functional feedback, fix it as `r2`, and continue with small visible increments. Do not spend the development cycle on speculative architecture.
