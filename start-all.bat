@echo off
chcp 65001 >nul
echo ========================================
echo   RS Urban Monitor - Start All
echo ========================================
echo.
echo [1/3] Starting GeoServer...
start "GeoServer" "C:\Users\19161\Desktop\rs-urban-monitor\start-geoserver.bat"
echo [2/3] Starting Frontend...
start "Frontend" /D "C:\Users\19161\Desktop\rs-urban-monitor" cmd /c "set PATH=D:\software\node;%%PATH%% && npx vite --host 0.0.0.0"
echo [3/3] Starting ngrok...
start "ngrok" cmd /k "cd /d C:\Users\19161\Desktop\rs-urban-monitor && ngrok.exe http 5173"
echo.
echo ========================================
echo   GeoServer : http://127.0.0.1:8080/geoserver
echo   Frontend  : http://127.0.0.1:5173
echo   ngrok URL : check ngrok window
echo ========================================
timeout /t 5
