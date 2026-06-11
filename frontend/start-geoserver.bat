@echo off
chcp 65001 >nul 2>&1

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
set "GEOSERVER_HOME=%PROJECT_ROOT%\geoserver-2.25.5-bin"
set "GEOSERVER_BIN=%GEOSERVER_HOME%\bin"

if not exist "%GEOSERVER_BIN%\startup.bat" (
    echo [ERROR] GeoServer startup script not found:
    echo %GEOSERVER_BIN%\startup.bat
    pause
    exit /b 1
)

if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\java.exe" goto :java_found
)

if exist "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
    goto :java_found
)

for /d %%J in ("%ProgramFiles%\Microsoft\jdk*") do (
    if exist "%%~fJ\bin\java.exe" set "JAVA_HOME=%%~fJ"
)
if defined JAVA_HOME goto :java_found

for /d %%J in ("%ProgramFiles%\Eclipse Adoptium\jdk*") do (
    if exist "%%~fJ\bin\java.exe" set "JAVA_HOME=%%~fJ"
)
if defined JAVA_HOME goto :java_found

for /d %%J in ("%ProgramFiles%\Java\jdk*") do (
    if exist "%%~fJ\bin\java.exe" set "JAVA_HOME=%%~fJ"
)
if defined JAVA_HOME goto :java_found

where java >nul 2>&1
if %errorlevel%==0 goto :java_on_path

echo [ERROR] Java runtime not found. Install JDK 17 or set JAVA_HOME.
pause
exit /b 1

:java_found
set "PATH=%JAVA_HOME%\bin;%PATH%"
echo JAVA_HOME=%JAVA_HOME%
goto :start_geoserver

:java_on_path
echo JAVA_HOME is not set; using java from PATH.

:start_geoserver
echo GEOSERVER_HOME=%GEOSERVER_HOME%
echo.
cd /d "%GEOSERVER_BIN%"
call startup.bat
