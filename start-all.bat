@echo off
chcp 65001 >nul
echo ========================================
echo   RS Urban Monitor - Start All
echo ========================================
echo.

:: ── Detect Python 3.10+ ──
set "PYTHON_EXE="

:: Method 1: py launcher -3 (most reliable on Windows with multiple versions)
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=2 delims= " %%v in ('py -3 --version 2^>^&1') do set "PY_VER=%%v"
    set "PYTHON_EXE=py -3"
    goto :py_found
)

:: Method 2: python command
python --version >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    set "PYTHON_EXE=python"
    goto :py_found
)

:: Method 3: backend-bundled portable Python fallback
if exist "%USERPROFILE%\Desktop\UEEA2601_upload\python311-embed\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\Desktop\UEEA2601_upload\python311-embed\python.exe"
    set "PY_VER=3.11.9-portable"
    goto :py_found
)

:: Method 4: direct path
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    set "PY_VER=3.11.x"
    goto :py_found
)

echo [ERROR] Python 3.10+ not found!
echo Please install Python 3.10 or later from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:py_found
echo [Python] %PYTHON_EXE% = %PY_VER%
echo.

echo [1/4] Starting GeoServer...
start "GeoServer" "C:\Users\19161\Desktop\rs-urban-monitor\start-geoserver.bat"
echo [2/4] Starting Backend (FastAPI)...
start "Backend" cmd /k "cd /d C:\Users\19161\Desktop\UEEA2601_upload && set PYTHONPATH=%%CD%%;%%PYTHONPATH%% && %PYTHON_EXE% -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo [3/4] Starting Frontend (Vite)...
start "Frontend" /D "C:\Users\19161\Desktop\rs-urban-monitor" cmd /c "set PATH=D:\software\node;%%PATH%% && npx vite --host 0.0.0.0"
echo [4/4] Starting ngrok...
start "ngrok" cmd /k "cd /d C:\Users\19161\Desktop\rs-urban-monitor && ngrok.exe http 5173"
echo.
echo ========================================
echo   GeoServer : http://127.0.0.1:8080/geoserver
echo   Backend   : http://127.0.0.1:8001
echo   Frontend  : http://127.0.0.1:5173
echo   ngrok URL : check ngrok window
echo ========================================
timeout /t 5
