@echo off
chcp 65001 >nul 2>&1

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"

if exist "%PROJECT_ROOT%\start-all.bat" (
    call "%PROJECT_ROOT%\start-all.bat" %*
) else (
    echo [ERROR] Root launcher not found:
    echo %PROJECT_ROOT%\start-all.bat
    pause
    exit /b 1
)
