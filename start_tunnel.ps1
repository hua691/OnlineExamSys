# ================================================================
# One-click: Django + Cloudflare Tunnel, expose public URL
# ================================================================
# Usage:
#   1. In PowerShell run:   .\start_tunnel.ps1
#   2. Wait ~10 seconds and look for the https://xxx.trycloudflare.com line
#   3. Share that URL with your teacher/classmates
#   4. To stop: Ctrl+C in this window, Django window will auto-close
# ================================================================

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Online Exam System - Public Tunnel " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---- 1. Ensure cloudflared.exe exists ----
$cf = Join-Path $PSScriptRoot 'deploy\cloudflared.exe'
if (!(Test-Path $cf)) {
    Write-Host "ERROR: deploy\cloudflared.exe not found" -ForegroundColor Red
    exit 1
}

# ---- 2. Start Django in a new window ----
Write-Host "[1/2] Starting Django on port 8000 (new window)..." -ForegroundColor Yellow
$djangoProc = Start-Process powershell -ArgumentList @(
    '-NoExit',
    '-Command',
    "Set-Location '$PSScriptRoot'; python manage.py runserver 127.0.0.1:8000"
) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 4

$listening = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue
if (!$listening.TcpTestSucceeded) {
    Write-Host "      Django not ready yet, waiting 5 more seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# ---- 3. Start Cloudflare Tunnel (foreground) ----
Write-Host ""
Write-Host "[2/2] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "      LOOK for the https://xxx.trycloudflare.com line below" -ForegroundColor Green
Write-Host "      Copy that URL and share it." -ForegroundColor Green
Write-Host ""

try {
    & $cf tunnel --url http://localhost:8000 --loglevel info
}
finally {
    Write-Host ""
    Write-Host "Tunnel stopped" -ForegroundColor Red
    try {
        Stop-Process -Id $djangoProc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "Django process stopped" -ForegroundColor Green
    } catch {}
}
