# TransportERP-UA v0.2 TEST r8.1

Дата: 17.09.2026

Hotfix до оглядового prerelease v0.2-r8.

## Виправлено

- Windows x64 `--windowed` launcher більше не падає під час старту Uvicorn через відсутні `sys.stdout` / `sys.stderr` у PyInstaller GUI-процесі.
- Локальний Uvicorn тепер запускається з console-independent logging configuration (`log_config=None`).
- Packaged preflight тепер створює саме ту Uvicorn-конфігурацію, що використовується при реальному запуску, щоб цей клас помилки ловився в GitHub Actions до публікації EXE.

## Пакети

- START ZIP;
- Windows x64 Portable ZIP;
- Windows x64 Setup EXE;
- macOS arm64 Portable ZIP;
- macOS x86_64 Portable ZIP;
- SHA256SUMS.

## Дані

Робоча база даних не входить до жодного релізного архіву.

Windows: `%LOCALAPPDATA%\TransportERP-UA`

macOS: `~/Library/Application Support/TransportERP-UA`

Це тестовий prerelease. macOS-збірки ad-hoc signed і не notarized. Windows installer не має комерційного code-signing certificate.
