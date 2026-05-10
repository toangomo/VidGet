@echo off
chcp 65001 >nul
echo Khoi dong VidGet Web...
echo.
echo Backend : http://localhost:8000
echo Frontend: http://localhost:3000
echo.

:: Mo backend trong cua so moi
start "VidGet Backend" cmd /k "cd /d "%~dp0backend" && py -m uvicorn main:app --reload --port 8000"

:: Doi 2 giay de backend khoi dong truoc
timeout /t 2 /nobreak >nul

:: Mo frontend trong cua so moi
start "VidGet Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Mo trinh duyet sau 4 giay
timeout /t 4 /nobreak >nul
start http://localhost:3000
