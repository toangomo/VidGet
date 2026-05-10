@echo off
echo ============================================
echo   VidGet Web - Install dependencies
echo ============================================
echo.

echo [1/2] Installing Python packages (backend)...
py -m pip install fastapi "uvicorn[standard]" yt-dlp python-multipart
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo.

echo [2/2] Installing Node.js packages (frontend)...
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js at: https://nodejs.org
    pause
    exit /b 1
)
cd /d "%~dp0frontend"
npm install
echo.

echo ============================================
echo   Done! Run start.bat to launch the app.
echo ============================================
pause
