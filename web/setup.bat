@echo off
chcp 65001 >nul
echo ============================================
echo   VidGet Web - Cai dat lan dau
echo ============================================
echo.

echo [1/2] Cai thu vien Python (backend)...
py -m pip install fastapi "uvicorn[standard]" yt-dlp python-multipart
echo.

echo [2/2] Cai thu vien Node.js (frontend)...
cd /d "%~dp0frontend"
where npm >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay npm. Cai Node.js tai: https://nodejs.org
    pause
    exit /b 1
)
npm install
echo.

echo ============================================
echo   Cai dat hoan tat!
echo   Chay start.bat de khoi dong app.
echo ============================================
pause
