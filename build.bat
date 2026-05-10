@echo off
echo ============================================
echo   VidGet - Build .exe
echo ============================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not found. Run: py -m pip install pyinstaller
    pause
    exit /b 1
)

echo Building... please wait (1-3 minutes)
echo.

py -m PyInstaller --onefile --windowed --name "VidGet" --clean main.py

echo.
if exist "dist\VidGet.exe" (
    echo ============================================
    echo   SUCCESS! File: dist\VidGet.exe
    echo ============================================
    explorer dist
) else (
    echo [ERROR] Build failed. Check output above.
)
pause
