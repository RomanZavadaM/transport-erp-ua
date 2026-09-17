@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set /p APP_VERSION=<PREVIEW_VERSION.txt
set /p APP_REVISION=<PREVIEW_REVISION.txt
set "APP_VERSION_SAFE=%APP_VERSION:.=_%"
set "BUNDLE_DIR=TransportERP-UA_v%APP_VERSION_SAFE%_TEST_%APP_REVISION%_Windows_x64"
set "BUNDLE_ZIP=%BUNDLE_DIR%_Portable.zip"

echo [TransportERP-UA v%APP_VERSION% TEST %APP_REVISION%] Building frontend...
pushd frontend
call npm install
if errorlevel 1 goto :fail_pop
call npm run lint
if errorlevel 1 goto :fail_pop
call npm run typecheck
if errorlevel 1 goto :fail_pop
call npm run build
if errorlevel 1 goto :fail_pop
popd

echo [TransportERP-UA] Installing Python build dependencies...
py -3.12 -m pip install --upgrade pip
if errorlevel 1 goto :fail
py -3.12 -m pip install -e ".\backend[desktop,dev]" "pyinstaller>=6.10,<7.0"
if errorlevel 1 goto :fail

echo [TransportERP-UA] Running backend checks...
pushd backend
py -3.12 -m ruff check .
if errorlevel 1 goto :fail_pop
py -3.12 -m mypy
if errorlevel 1 goto :fail_pop
py -3.12 -m pytest -q
if errorlevel 1 goto :fail_pop
popd

echo [TransportERP-UA] Building Windows onedir from TransportERP.spec...
if exist "dist\TransportERP-UA" rmdir /s /q "dist\TransportERP-UA"
if exist "dist\%BUNDLE_DIR%" rmdir /s /q "dist\%BUNDLE_DIR%"
py -3.12 -m PyInstaller --noconfirm --clean TransportERP.spec
if errorlevel 1 goto :fail
move "dist\TransportERP-UA" "dist\%BUNDLE_DIR%" >nul
if errorlevel 1 goto :fail

if not exist "dist\%BUNDLE_DIR%\TransportERP-UA.exe" goto :fail
for /r "dist\%BUNDLE_DIR%" %%F in (*.db *.sqlite *.sqlite3) do (
    echo ERROR: database unexpectedly bundled: %%F
    goto :fail
)

echo [TransportERP-UA] Running packaged preflight...
set "TRANSPORT_ERP_SMOKE_TEST_ONLY=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Start-Process -FilePath 'dist\%BUNDLE_DIR%\TransportERP-UA.exe' -PassThru; if(-not $p.WaitForExit(30000)){Stop-Process -Id $p.Id -Force; exit 124}; exit $p.ExitCode"
set "TRANSPORT_ERP_SMOKE_TEST_ONLY="
if errorlevel 1 goto :fail

echo [TransportERP-UA] Creating portable ZIP...
if exist "%BUNDLE_ZIP%" del /q "%BUNDLE_ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%BUNDLE_DIR%' -DestinationPath '%BUNDLE_ZIP%' -Force"
if errorlevel 1 goto :fail
powershell -NoProfile -Command "$h=(Get-FileHash '%BUNDLE_ZIP%' -Algorithm SHA256).Hash.ToLower(); Set-Content -Encoding ascii -Path 'SHA256SUMS_v%APP_VERSION_SAFE%_TEST_%APP_REVISION%_Windows_x64.txt' -Value ($h + '  %BUNDLE_ZIP%')"
if errorlevel 1 goto :fail

echo Portable build ready: %BUNDLE_ZIP%
echo User data remains outside the program package.
exit /b 0

:fail_pop
popd
:fail
echo Build failed.
exit /b 1
