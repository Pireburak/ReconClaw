<#
.SYNOPSIS
    ReconClaw Test Runner for Windows / PowerShell
.DESCRIPTION
    Runs pytest test suite using uv with execution timing and reporting.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$StartTime = Get-Date
$env:UV_LINK_MODE = "copy"

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
    exit 1
}

$hasVenv = (Test-Path ".venv\Scripts\python.exe") -or (Test-Path ".venv\bin\python.exe") -or (Test-Path ".venv\bin\python")
if (-not $hasVenv) {
    Write-Host "  ▸ Initializing test virtualenv at .venv..." -ForegroundColor Blue
    & $uvBin venv .venv
}

& $uvBin run python -c "import pytest, pytest_asyncio" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ▸ Installing test dependencies via uv..." -ForegroundColor Blue
    & $uvBin pip install -r requirements.txt pytest pytest-asyncio | Out-Null
}

Write-Host "❯ Running ReconClaw Test Suite with uv...`n" -ForegroundColor Magenta

& $uvBin run pytest -v $args

$EndTime = Get-Date
$Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds)

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✔ All tests passed successfully in ${Duration}s.`n" -ForegroundColor Green
} else {
    Write-Host "`n✖ Test suite failed with exit code $LASTEXITCODE.`n" -ForegroundColor Red
    exit $LASTEXITCODE
}
