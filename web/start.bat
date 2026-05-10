@echo off
echo Starting VidGet Web...
echo.
echo Backend : http://localhost:8000
echo Frontend: http://localhost:3000
echo.

start "VidGet Backend" cmd /k "cd /d "%~dp0backend" && py -m uvicorn main:app --port 8000"

timeout /t 2 /nobreak >nul

start "VidGet Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 4 /nobreak >nul
start http://localhost:3000
