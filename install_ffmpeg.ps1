#Requires -RunAsAdministrator
$host.UI.RawUI.WindowTitle = "VidGet - Cai dat ffmpeg"
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  VidGet - Cai dat ffmpeg" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Kiem tra da co ffmpeg chua
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "[OK] ffmpeg da duoc cai dat san roi!" -ForegroundColor Green
    Write-Host "Ban khong can lam gi them."
    Write-Host ""
    Read-Host "Nhan Enter de dong"
    exit 0
}

Write-Host "Chua tim thay ffmpeg. Bat dau cai dat..." -ForegroundColor Yellow
Write-Host ""

# Thu 1: Winget
$winget = Get-Command winget -ErrorAction SilentlyContinue
if ($winget) {
    Write-Host "[1/2] Thu cai qua winget..." -ForegroundColor Cyan
    try {
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[OK] Cai ffmpeg thanh cong qua winget!" -ForegroundColor Green
            Write-Host "Hay khoi dong lai VidGet.exe de ap dung." -ForegroundColor Yellow
            Write-Host ""
            Read-Host "Nhan Enter de dong"
            exit 0
        }
    } catch {}
    Write-Host "[!] Winget that bai, thu cach khac..." -ForegroundColor Yellow
    Write-Host ""
}

# Thu 2: Tai truc tiep va cai thu cong
Write-Host "[2/2] Dang tai ffmpeg tu gyan.dev..." -ForegroundColor Cyan
Write-Host "(Co the mat 1-3 phut tuy toc do mang)"
Write-Host ""

$zipUrl  = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipPath = "$env:TEMP\ffmpeg.zip"
$destDir = "$env:ProgramFiles\ffmpeg"

try {
    # Tai file
    Write-Host "  Dang tai..." -NoNewline
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Write-Host " Xong!" -ForegroundColor Green

    # Giai nen
    Write-Host "  Dang giai nen..." -NoNewline
    if (Test-Path $destDir) { Remove-Item $destDir -Recurse -Force }
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
    Write-Host " Xong!" -ForegroundColor Green

    # Tim duong dan toi ffmpeg.exe
    $ffmpegExe = Get-ChildItem $destDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if (-not $ffmpegExe) { throw "Khong tim thay ffmpeg.exe sau khi giai nen." }
    $binPath = $ffmpegExe.DirectoryName

    # Them vao System PATH
    Write-Host "  Them vao PATH..." -NoNewline
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$binPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$binPath", "Machine")
    }
    Write-Host " Xong!" -ForegroundColor Green

    # Don dep
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  [OK] CAI FFMPEG THANH CONG!" -ForegroundColor Green
    Write-Host "  Hay khoi dong lai VidGet.exe de ap dung." -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  [LOI] $_" -ForegroundColor Red
    Write-Host "  Tai thu cong tai: https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Red
}

Write-Host ""
Read-Host "Nhan Enter de dong"
