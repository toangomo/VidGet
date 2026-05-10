@echo off
chcp 65001 >nul
echo ============================================
echo   VidGet - Build file .exe
echo ============================================
echo.

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [LỖI] Không tìm thấy PyInstaller.
    echo Chạy install.bat trước.
    pause
    exit /b 1
)

echo Đang build... (có thể mất 1-3 phút)
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "VidGet" ^
    --clean ^
    main.py

echo.
if exist "dist\VidGet.exe" (
    echo ============================================
    echo   BUILD THÀNH CÔNG!
    echo   File: dist\VidGet.exe
    echo ============================================
    explorer dist
) else (
    echo [LỖI] Build thất bại. Kiểm tra lại thư viện.
)
pause
