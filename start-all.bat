@echo off
chcp 65001 >nul 2>&1
set "SCRIPT_DIR=%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-all.ps1" %*
if errorlevel 1 (
    echo.
    echo [ERROR] start-all.ps1 failed.
    pause
)
