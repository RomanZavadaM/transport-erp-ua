@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title TransportERP-UA Preview

echo ==============================================
echo   TransportERP-UA - local Python preview
echo ==============================================
echo.

set "PY_CMD="

py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3.12"

if not defined PY_CMD (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    echo [ERROR] Python 3.12 or newer was not found.
    echo Install Python 3.12+ and enable the Python launcher or PATH option.
    echo.
    pause
    exit /b 1
)

if not exist "frontend\out\index.html" (
    echo [ERROR] Prepared frontend was not found: frontend\out\index.html
    echo Use the START ZIP produced by the project workflow.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating local Python environment...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :fail
)

set "VENV_PY=%CD%\.venv\Scripts\python.exe"

"%VENV_PY%" -c "import fastapi, uvicorn, webview, transport_erp" >nul 2>nul
if errorlevel 1 (
    echo [2/3] Installing TransportERP-UA dependencies...
    "%VENV_PY%" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    "%VENV_PY%" -m pip install ".\backend[desktop]"
    if errorlevel 1 goto :fail
) else (
    echo [2/3] Python environment is ready.
)

set "TRANSPORT_ERP_DEPLOYMENT_PROFILE=local"
set "TRANSPORT_ERP_ENVIRONMENT=local"
set "TRANSPORT_ERP_FRONTEND_DIR=%CD%\frontend\out"

echo [3/3] Starting TransportERP-UA...
echo.
"%VENV_PY%" -m transport_erp.desktop
if errorlevel 1 goto :fail

exit /b 0

:fail
echo.
echo [ERROR] TransportERP-UA could not be started.
echo Leave this window open and send a screenshot of the error.
echo.
pause
exit /b 1
