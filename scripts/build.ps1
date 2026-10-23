<#
.SYNOPSIS
    ReconClaw Build and Verification Engine for Windows / PowerShell
.DESCRIPTION
    Multi-phase build verification: Bytecode compilation, module imports,
    schema migrations, and Jinja2 template sanity checking.
#>

param(
    [switch]$Docker
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$StartTime = Get-Date
$env:UV_LINK_MODE = "copy"

Write-Host "  ____                       ____        _ _     _ " -ForegroundColor Magenta
Write-Host " |  _ \ ___  ___ ___  _ __  | __ ) _   _(_) | __| |" -ForegroundColor Magenta
Write-Host " | |_) / _ \/ __/ _ \| '_ \ |  _ \| | | | | |/ _\` |" -ForegroundColor Magenta
Write-Host " |  _ <  __/ (_| (_) | | | || |_) | |_| | | | (_| |" -ForegroundColor Magenta
Write-Host " |_| \_\___|\___\___/|_| |_||____/ \__,_|_|_|\__,_|" -ForegroundColor Magenta
Write-Host "  Build Validation, Bytecode Compilation & Integrity Suite`n" -ForegroundColor DarkGray

# 1. Detect uv binary
Write-Host "❯ Phase 1: Environment & Package Manager Verification" -ForegroundColor Cyan

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
    Write-Host "  ▸ Initializing build virtualenv at .venv..." -ForegroundColor Blue
    & $uvBin venv .venv
}

Write-Host "  ▸ Synchronizing dependencies via uv..." -ForegroundColor Blue
& $uvBin pip install -r requirements.txt pytest pytest-asyncio | Out-Null
Write-Host "  ✔ Environment & dependencies verified." -ForegroundColor Green

# 2. Bytecode compilation
Write-Host "`n❯ Phase 2: Bytecode Compilation & Syntax Verification" -ForegroundColor Cyan
Write-Host "  ▸ Compiling core modules and entrypoints..." -ForegroundColor Blue
$compiledCount = & $uvBin run python -c "
import py_compile, os, sys
count = 0
files = ['main.py', 'manage.py']
for base in ['core', 'tests']:
    for root, _, fs in os.walk(base):
        for f in fs:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
for path in files:
    try:
        py_compile.compile(path, doraise=True)
        count += 1
    except py_compile.PyCompileError as e:
        sys.stderr.write(f'Syntax error in {path}:\n{e}\n')
        sys.exit(1)
print(count)
"

if ($LASTEXITCODE -ne 0) {
    Write-Host "✖ Bytecode compilation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  ✔ Successfully compiled $compiledCount Python source files with 0 syntax errors." -ForegroundColor Green

# 3. Module imports
Write-Host "`n❯ Phase 3: Module Import & Architectural Integrity" -ForegroundColor Cyan
Write-Host "  ▸ Validating module imports..." -ForegroundColor Blue
& $uvBin run python -c "
import sys
modules = ['core.config', 'core.db_manager', 'core.engine', 'core.intel', 'core.ai', 'core.monitor', 'core.auth', 'main']
for mod in modules:
    __import__(mod)
    print(f'    \033[0;32m✔\033[0m Loaded {mod}')
"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✖ Module import check failed." -ForegroundColor Red
    exit 1
}
Write-Host "  ✔ All core modules imported cleanly without missing dependencies." -ForegroundColor Green

# 4. Database schema test
Write-Host "`n❯ Phase 4: Database Schema Sanity Test" -ForegroundColor Cyan
Write-Host "  ▸ Running isolated schema migration against temporary database..." -ForegroundColor Blue
& $uvBin run python -c "
import tempfile, os
from core.db_manager import init_db, get_db_connection

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
    temp_db_path = tf.name

try:
    os.environ['RECONCLAW_DB'] = temp_db_path
    init_db()
    conn = get_db_connection()
    tables = [row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
    expected = {'scans', 'open_ports', 'findings', 'users'}
    missing = expected - set(tables)
    if missing:
        raise RuntimeError(f'Missing expected tables: {missing}')
    conn.close()
finally:
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass
"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✖ Database schema verification failed." -ForegroundColor Red
    exit 1
}
Write-Host "  ✔ Database schema initialized and verified." -ForegroundColor Green

# 5. Templates validation
Write-Host "`n❯ Phase 5: Jinja2 Template Syntax Verification" -ForegroundColor Cyan
Write-Host "  ▸ Validating all HTML templates in templates/..." -ForegroundColor Blue
& $uvBin run python -c "
import os
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
count = 0
for root, _, files in os.walk('templates'):
    for f in files:
        if f.endswith('.html'):
            rel_path = os.path.relpath(os.path.join(root, f), 'templates')
            env.get_template(rel_path)
            count += 1
print(f'    \033[0;32m✔\033[0m Verified {count} Jinja2 templates')
"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✖ Template validation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  ✔ All frontend HTML templates parsed and validated." -ForegroundColor Green

# 6. Docker build (optional)
if ($Docker) {
    Write-Host "`n❯ Phase 6: Container Image Build" -ForegroundColor Cyan
    Write-Host "  ▸ Building Docker image 'reconclaw:latest'..." -ForegroundColor Blue
    docker build -t reconclaw:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✖ Docker build failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✔ Docker container image built successfully: reconclaw:latest" -ForegroundColor Green
}

$EndTime = Get-Date
$Duration = [math]::Round(($EndTime - $StartTime).TotalSeconds)

Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "  ✨ ReconClaw build and integrity verification PASSED!" -ForegroundColor Green
Write-Host "  Total duration: ${Duration}s" -ForegroundColor White
Write-Host "  Status:         READY FOR DEPLOYMENT / TESTING" -ForegroundColor Green
Write-Host "========================================================================`n" -ForegroundColor Green
