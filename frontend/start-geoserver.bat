@echo off
set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
echo JAVA_HOME=%JAVA_HOME%
echo.
cd /d "C:\Users\19161\Desktop\rs-urban-monitor\geoserver-2.25.5-bin\bin"
call startup.bat
