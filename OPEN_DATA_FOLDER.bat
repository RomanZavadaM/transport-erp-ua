@echo off
setlocal EnableExtensions

if defined LOCALAPPDATA (
    set "DATA_DIR=%LOCALAPPDATA%\TransportERP-UA"
) else if defined APPDATA (
    set "DATA_DIR=%APPDATA%\TransportERP-UA"
) else (
    set "DATA_DIR=%USERPROFILE%\TransportERP-UA-Data"
)

if not exist "%DATA_DIR%" mkdir "%DATA_DIR%" >nul 2>nul
start "" "%DATA_DIR%"
