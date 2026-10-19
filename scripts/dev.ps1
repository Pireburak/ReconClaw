<#
.SYNOPSIS
    ReconClaw Development Server Runner for Windows / PowerShell
.DESCRIPTION
    Automates uv environment validation, dependency installation, .env provisioning,
    and launches Uvicorn with live hot reload.
#>

param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$env:UV_LINK_MODE = "copy"

Write-Host "  ____                         ____ _                 " -ForegroundColor Magenta
Write-Host " |  _ \ ___  ___ ___  _ __    / ___| | __ ___      __ " -ForegroundColor Magenta
Write-Host " | |_) / _ \/ __/ _ \| '_ \  | |   | |/ _\` \ \ /\ / / " -ForegroundColor Magenta
Write-Host " |  _ <  __/ (_| (_) | | | | | |___| | (_| |\ V  V /  " -ForegroundColor Magenta
Write-Host " |_| \_\___|\___\___/|_| |_|  \____|_|\__,_| \_/\_/   " -ForegroundColor Magenta
Write-Host "  Asynchronous Attack Surface Reconnaissance & Intel Pipeline`n" -ForegroundColor DarkGray

# 1. Detect uv binary
Write-Host "❯ Phase 1: Validating runtime environment and package manager..." -ForegroundColor Cyan

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
$uvBin = ""

if ($uvCmd) {
    $uvBin = $uvCmd.Source
} else {
    $candidates = @(
        "$env:USERPROFILE\.cargo\bin\uv.exe",
        "$env:LOCALAPPDATA\bin\uv.exe",
        "C:\Program Files\uv\uv.exe"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $uvBin = $cand
            break
        }
    }
}

if (-not $uvBin) {
    Write-Host "✖ Astral 'uv' was not found on your system." -ForegroundColor Red
    Write-Host "  Please install uv by running:" -ForegroundColor Yellow
    Write-Host "    powershell -c ""irm https://astral.sh/uv/install.ps1 | iex""" -ForegroundColor White
    exit 1
}

$uvVersion = & $uvBin --version
Write-Host "  ▸ Using uv: $uvBin ($uvVersion)" -ForegroundColor DarkGray

# 2. Check virtual environment
Write-Host "❯ Phase 2: Checking isolated virtual environment..." -ForegroundColor Cyan
$hasVenv = (Test-Path ".venv\Scripts\python.exe") -or (Test-Path ".venv\bin\python.exe") -or (Test-Path ".venv\bin\python")

if (-not $hasVenv) {
    Write-Host "  ▸ Creating virtual environment at .venv..." -ForegroundColor Blue
    & $uvBin venv .venv
    Write-Host "  ✔ Virtual environment initialized." -ForegroundColor Green
} else {
    Write-Host "  ✔ Virtual environment verified at .venv." -ForegroundColor Green
}

# 3. Check dependencies
Write-Host "❯ Phase 3: Verifying application dependencies..." -ForegroundColor Cyan
& $uvBin run python -c "import fastapi, uvicorn, jinja2, pydantic, httpx" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ▸ Synchronizing dependencies via uv..." -ForegroundColor Blue
    & $uvBin pip install -r requirements.txt pytest pytest-asyncio
    Write-Host "  ✔ Dependencies successfully synchronized." -ForegroundColor Green
} else {
    Write-Host "  ✔ All core dependencies verified and ready." -ForegroundColor Green
}

# 4. Environment & database provisioning
Write-Host "❯ Phase 4: Checking environment configuration and storage..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "  ▸ Generating .env from .env.example..." -ForegroundColor Blue
        Copy-Item ".env.example" ".env"
        & $uvBin run python -c "import secrets, re; text = open('.env', 'r', encoding='utf-8').read(); key = secrets.token_hex(32); open('.env', 'w', encoding='utf-8').write(re.sub(r'SECRET_KEY=degistirilmeli_cok_gizli_anahtar', f'SECRET_KEY={key}', text))"
        Write-Host "  ✔ Default .env generated with random SECRET_KEY." -ForegroundColor Green
    }
} else {
    Write-Host "  ✔ Environment file .env active." -ForegroundColor Green
}

if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

& $uvBin run python -c "from core.db_manager import init_db; init_db()"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✖ Database initialization failed." -ForegroundColor Red
    exit 1
}
Write-Host "  ✔ Database initialized and schema verified." -ForegroundColor Green

# 5. Launch development server
Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "  🚀 ReconClaw Dev Server starting with live hot reload!" -ForegroundColor Green
Write-Host "  URL:           http://${HostName}:${Port}" -ForegroundColor Cyan
Write-Host "  Documentation: http://${HostName}:${Port}/docs" -ForegroundColor Cyan
Write-Host "  Watcher dirs:  main.py, core\, templates\, static\" -ForegroundColor White
Write-Host "========================================================================`n" -ForegroundColor Green

try {
    & $uvBin run uvicorn main:app `
        --reload `
        --reload-dir main.py `
        --reload-dir core `
        --reload-dir templates `
        --host $HostName `
        --port $Port `
        --proxy-headers
} catch {
    Write-Host "`n✖ Dev server encountered an unexpected error." -ForegroundColor Red
}

if ($LASTEXITCODE -ne 0) {
    # Check if port is occupied
    $portBusy = & $uvBin run python -c "import socket; s = socket.socket(); (s.bind(('$HostName', $Port)), print('0')) if True else print('1')" 2>$null
    if ($portBusy -ne "0") {
        Write-Host "  Diagnostic: Port $Port appears to be in use." -ForegroundColor Yellow
        Write-Host "  To run on another port: .\scripts\dev.ps1 -Port 8080" -ForegroundColor White
    }
    exit $LASTEXITCODE
}
