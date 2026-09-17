@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set /p APP_VERSION=<PREVIEW_VERSION.txt
set /p APP_REVISION=<PREVIEW_REVISION.txt
set "APP_VERSION_SAFE=%APP_VERSION:.=_%"
set "BUNDLE_DIR=dist\TransportERP-UA_v%APP_VERSION_SAFE%_TEST_%APP_REVISION%_Windows_x64"
set "SETUP_NAME=TransportERP-UA_v%APP_VERSION_SAFE%_TEST_%APP_REVISION%_Setup_Windows_x64"

if not exist "%BUNDLE_DIR%\TransportERP-UA.exe" (
    echo Portable bundle not found. Run BUILD_WINDOWS.bat first.
    exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo Inno Setup 6 not found.
    echo Install Inno Setup 6 and run this script again.
    exit /b 1
)

"%ISCC%" "/DMyAppVersion=%APP_VERSION%-%APP_REVISION%" "/DBundleDir=%BUNDLE_DIR%" "/DOutputBaseFilename=%SETUP_NAME%" "installer\TransportERP-UA.iss"
if errorlevel 1 exit /b 1

if not exist "release_out\%SETUP_NAME%.exe" (
    echo Installer output not found.
    exit /b 1
)

echo Installer ready: release_out\%SETUP_NAME%.exe
exit /b 0
