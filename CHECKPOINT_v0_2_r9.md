# TransportERP-UA — CHECKPOINT v0.2 TEST r9

Date: 2026-09-17

## Goal

Align TransportERP-UA release preparation with the already proven Taxo workflow so local builds and GitHub builds use the same recipes.

## Added

- `START.bat` — stable user-facing launch entry point;
- `BUILD_START.sh` — reproducible START package builder;
- `BUILD_WINDOWS.bat` — Windows tests + frontend build + PyInstaller onedir + packaged preflight + Portable ZIP + SHA256;
- `BUILD_INSTALLER.bat` — Inno Setup installer build from the already verified portable bundle;
- `BUILD_MACOS.sh` — native macOS tests + PyInstaller app + architecture check + ad-hoc codesign + packaged preflight + Portable ZIP + SHA256;
- `TransportERP.spec` — canonical Windows executable recipe;
- `TransportERP_macos.spec` — canonical macOS executable recipe;
- `RELEASE_CHECKLIST.md` — Taxo-style release discipline;
- `.github/workflows/publish-control-release.yml` — manual control-release workflow that invokes repository build recipes instead of maintaining separate CI-only PyInstaller commands.

## Preserved rules

- database/documents/backups live outside program version folders;
- no SQLite files are bundled in START/Portable/Setup/app artifacts;
- every archive has a unique versioned root folder;
- everyday testing remains Python/START-first;
- executable control builds are periodic, approximately every 5–10 working revisions or at major checkpoints;
- Windows packaged preflight explicitly covers the `--windowed` launcher path that caused the v0.2-r8 failure.

## Previous published executable

`v0.2-r8.1` — Windows launcher hotfix, with successful Windows windowed bundle verification and macOS arm64/x86_64 builds.

## Next

After this release-process checkpoint is green, continue STOIR/technical service: block dispatcher release for vehicles with active blocking technical defects or repair orders, then continue scheduled inspections and technical documentation.
