# TransportERP-UA — CHECKPOINT v0.2 TEST r1

Date: 2026-09-16

## Current development version

- Version: **v0.2 TEST r1**.
- Working branch: `work/v0.2-python-preview-r1`.
- Primary test package: `TransportERP-UA_v0.2_TEST_r1_START.zip`.
- Primary launch method during development: `START_WINDOWS.bat` → local `.venv` → Python desktop application.
- EXE is **not** the normal development cycle. Windows executable packages are control builds made manually about every 5–10 working revisions or when a stable milestone needs to be frozen.

## Testing and publication practice

The project follows the proven Taxo workflow:

1. Work on a numbered candidate/revision.
2. Run backend/frontend automated tests.
3. Build a START/source preview ZIP with a unique versioned root folder.
4. Test that ZIP manually on a real Windows workstation.
5. Fix practical UI/functional issues before expanding scope.
6. Record the accepted point in `CHECKPOINT_CURRENT.md` and a version-specific checkpoint.
7. Every ~5–10 working revisions, or at an important milestone, build and verify a Windows EXE/portable control package.
8. Control executable packages receive SHA256 checksums and may be published as a GitHub prerelease/release checkpoint.

## Archive naming rule

Every archive must have a unique version in both places:

- ZIP filename: `TransportERP-UA_v0.2_TEST_r1_START.zip`
- Root folder inside ZIP: `TransportERP-UA_v0.2_TEST_r1_START/`

A later build must use a different folder name (`r2`, `r3`, etc.) so extracted builds never overwrite or mix with each other by accident.

## Current visible functionality

- desktop-style local application shell;
- local SQLite storage;
- enterprise settings;
- vehicles list, editing and vehicle card;
- vehicle documents;
- odometer history;
- drivers list, editing and driver card;
- driver documents;
- stops;
- routes and ordered route stops;
- local system status;
- ZIP backup creation.

## Local data

- Business data are **not bundled** into START or executable packages.
- Runtime data remain outside the program package under the local TransportERP-UA user-data location.
- Test/release workflows reject bundled `.db`, `.sqlite` and `.sqlite3` files.

## Immediate goal

Do not expand architecture for its own sake. Use manual testing feedback from this START package to improve the actual application UI and workflow, then move to the next business function.
