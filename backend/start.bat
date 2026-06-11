@echo off
chcp 65001 >nul 2>&1
title UEEA2601 Backend Server
cd /d "%~dp0"

:: ── Detect Python 3.10+ ──
set "PYTHON_EXE="

:: Method 0: explicit override, e.g. set RS_URBAN_PYTHON=C:\Python311\python.exe
if defined RS_URBAN_PYTHON (
    if exist "%RS_URBAN_PYTHON%" (
        set "PYTHON_EXE=%RS_URBAN_PYTHON%"
        goto :py_found
    )
)

:: Method 1: py launcher -3 (avoids Python 2.7 from ArcGIS)
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=py -3"
    goto :py_found
)

:: Method 2: python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto :py_found
)

:: Method 3: bundled portable Python fallback
if exist "%~dp0python311-embed\python.exe" (
    set "PYTHON_EXE=%~dp0python311-embed\python.exe"
    goto :py_found
)

:: Method 4: direct path fallback
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :py_found
)

echo.
echo ============================================
echo   [ERROR] Python 3.10+ not found!
echo ============================================
echo.
echo   This backend requires Python 3.10 or later.
echo.
echo   Install from: https://www.python.org/downloads/
echo   During installation, check "Add Python to PATH".
echo.
echo   If you have Python installed but this message appears,
echo   try running:  py -3 main.py
echo   Or set:       set RS_URBAN_PYTHON=C:\path\to\python.exe
echo.
pause
exit /b 1

:py_found
echo ========================================
echo   UEEA2601 Backend - FastAPI Server
echo   http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo ========================================
echo.
echo [Python] %PYTHON_EXE%
echo.

set "PYTHONPATH=%CD%;%PYTHONPATH%"

:: Check Python version is 3.10+
%PYTHON_EXE% -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python 3.10+ is required. Detected version:
    %PYTHON_EXE% --version
    echo Some features may not work correctly.
    echo.
)

:: Check required packages
%PYTHON_EXE% -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing dependencies...
    %PYTHON_EXE% -m pip install -r requirements.txt
    echo.
)

echo [INFO] Starting server (uvicorn with --reload)...
echo [INFO] Press Ctrl+C to stop.
echo.
%PYTHON_EXE% -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
pause
