# TransportERP-UA — CURRENT CHECKPOINT

Date: 2026-09-17

## Current working revision

- Version: **v0.2 TEST r9**.
- Working branch: `work/r9-taxo-release-alignment`.
- Detailed checkpoint: `CHECKPOINT_v0_2_r9.md`.
- Previous published executable hotfix: `v0.2-r8.1`.
- Current development launch: `START.bat` / `START_WINDOWS.bat`.

## Persistent local data

All START/Portable/Setup revisions use persistent data outside the version folder.

Windows:
`%LOCALAPPDATA%\TransportERP-UA`

macOS:
`~/Library/Application Support/TransportERP-UA`

SQLite, documents and backups are never bundled into release packages. Changing or uninstalling a program version must not remove business data.

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
- completed maintenance/inspection history;
- technical service screen;
- defects with severity and blocking flag;
- repair orders, works, parts, materials, cost, completion and technical close;
- local ZIP backup.

## Project boundary with Taxo

TransportERP-UA owns fleet operations, technical management, STOIR, repairs, documents, mileage, fuel, release and waybills.

Taxo remains the specialized driver-worktime/tachograph subsystem: tachograph cards, driving/rest, Regulation №340 analysis, shift schedules, timesheets and activity confirmation forms.

## r9 release-process alignment

TransportERP now follows the proven Taxo release mechanics rather than keeping a separate GitHub-only build recipe:

- `START.bat` is the stable user-facing Python launch entry point;
- `BUILD_WINDOWS.bat` builds and verifies the Windows onedir/portable bundle;
- `BUILD_INSTALLER.bat` builds the Windows Setup EXE;
- `BUILD_MACOS.sh` builds and verifies native macOS bundles;
- `TransportERP.spec` and `TransportERP_macos.spec` are canonical PyInstaller recipes;
- `BUILD_START.sh` creates the versioned START package;
- `RELEASE_CHECKLIST.md` defines the release sequence;
- `.github/workflows/publish-control-release.yml` repeats those same repository build recipes instead of inventing a second CI-only build path.

## Packaging rule

Release packages use the Taxo naming style and always have unique versioned root folders. Business databases are forbidden in release artifacts. Executable control releases are made approximately every 5–10 working revisions or at a meaningful milestone, not on each minor commit.

## Next functional step

Continue the technical-service line: hard-block dispatcher release when a vehicle has an open blocking defect/repair, then expand STOIR documents, scheduled inspections, technical journals and maintenance documentation.
