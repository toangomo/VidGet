@echo off
:: Tu dong xin quyen Admin neu chua co
net session >nul 2>&1
if errorlevel 1 (
    powershell -WindowStyle Hidden -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
:: Chay file PowerShell chinh
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_ffmpeg.ps1"
