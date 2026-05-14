# ── VidGet — build standalone Windows exe ────────────────────────────────────

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== VidGet Build ===" -ForegroundColor Cyan

# ── Clean previous build ──────────────────────────────────────────────────────
if (Test-Path "dist\VidGet.exe") { Remove-Item "dist\VidGet.exe" -Force }
if (Test-Path "build")           { Remove-Item "build" -Recurse -Force }

# ── Run PyInstaller ───────────────────────────────────────────────────────────
Write-Host "Building VidGet.exe..." -ForegroundColor Yellow

pyinstaller `
  --onefile `
  --windowed `
  --name "VidGet" `
  --icon "VidGet.ico" `
  --version-file "version_info.txt" `
  --collect-all customtkinter `
  --collect-all yt_dlp `
  --hidden-import "PIL._tkinter_finder" `
  --hidden-import "PIL.ImageTk" `
  --hidden-import "tkinter" `
  --hidden-import "tkinter.font" `
  --hidden-import "tkinter.ttk" `
  --hidden-import "encodings" `
  --hidden-import "encodings.utf_8" `
  --hidden-import "encodings.ascii" `
  --hidden-import "encodings.cp1252" `
  --hidden-import "encodings.latin_1" `
  --hidden-import "encodings.idna" `
  --collect-submodules encodings `
  --clean `
  --noconfirm `
  main.py

# ── Result ────────────────────────────────────────────────────────────────────
if (Test-Path "dist\VidGet.exe") {
  $mb = [math]::Round((Get-Item "dist\VidGet.exe").Length / 1MB, 1)
  Write-Host ""
  Write-Host "Build thanh cong!" -ForegroundColor Green
  Write-Host "  File : dist\VidGet.exe" -ForegroundColor White
  Write-Host "  Size : $mb MB"          -ForegroundColor White
  Write-Host ""
  Write-Host "Tiep theo:" -ForegroundColor Cyan
  Write-Host "  1. Vao GitHub > Releases > Draft a new release"
  Write-Host "  2. Tag: v1.0.0  |  Title: VidGet v1.0.0"
  Write-Host "  3. Dinh kem file dist\VidGet.exe"
  Write-Host "  4. Publish release"
  Write-Host "  -> URL tai: https://github.com/toangomo/VidGet/releases/latest/download/VidGet.exe"
} else {
  Write-Host "Build that bai. Xem log phia tren." -ForegroundColor Red
  exit 1
}
