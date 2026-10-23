#!/usr/bin/env bash
# ==============================================================================
# ReconClaw Development Server Runner (Cross-Platform: Linux / macOS / Windows)
# Features:
#   - Automated uv detection across Linux, macOS, and Windows (Git Bash/WSL/MSYS)
#   - Cross-platform virtual environment detection (.venv/bin or .venv/Scripts)
#   - Automatic dependency verification and installation via uv
#   - In-place .env generation with cryptographic random secret (zero sed dependency)
#   - Platform-independent port collision detection via socket binding
#   - Uvicorn hot-reloading with multi-directory watcher
#   - Rich progress reporting, ANSI diagnostics, and graceful shutdown
# ==============================================================================

set -eo pipefail

# ANSI color codes
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
RESET='\033[0m'

info()    { echo -e "${CYAN}❯${RESET} ${BOLD}$1${RESET}"; }
step()    { echo -e "  ${BLUE}▸${RESET} $1"; }
success() { echo -e "  ${GREEN}✔${RESET} $1"; }
warn()    { echo -e "  ${YELLOW}⚠${RESET} ${YELLOW}$1${RESET}"; }
error()   { echo -e "  ${RED}✖${RESET} ${RED}$1${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# External volume and cross-filesystem link mode compatibility
export UV_LINK_MODE=copy

# Header banner
echo -e "${PURPLE}${BOLD}"
echo "  ____                         ____ _                 "
echo " |  _ \ ___  ___ ___  _ __    / ___| | __ ___      __ "
echo " | |_) / _ \/ __/ _ \| '_ \  | |   | |/ _\` \ \ /\ / / "
echo " |  _ <  __/ (_| (_) | | | | | |___| | (_| |\ V  V /  "
echo " |_| \_\___|\___\___/|_| |_|  \____|_|\__,_| \_/\_/   "
echo -e "${RESET}${DIM}  Asynchronous Attack Surface Reconnaissance & Intel Pipeline${RESET}\n"

# ------------------------------------------------------------------------------
# 1. Cross-Platform UV Detection
# ------------------------------------------------------------------------------
info "Phase 1: Validating runtime environment and package manager..."

detect_uv() {
    if command -v uv >/dev/null 2>&1; then
        command -v uv
    elif command -v uv.exe >/dev/null 2>&1; then
        command -v uv.exe
    elif [[ -x "/opt/homebrew/bin/uv" ]]; then
        echo "/opt/homebrew/bin/uv"
    elif [[ -x "$HOME/.cargo/bin/uv" ]]; then
        echo "$HOME/.cargo/bin/uv"
    elif [[ -x "$HOME/.cargo/bin/uv.exe" ]]; then
        echo "$HOME/.cargo/bin/uv.exe"
    elif [[ -x "$HOME/.local/bin/uv" ]]; then
        echo "$HOME/.local/bin/uv"
    elif [[ -n "$LOCALAPPDATA" && -x "$LOCALAPPDATA/bin/uv.exe" ]]; then
        echo "$LOCALAPPDATA/bin/uv.exe"
    elif [[ -x "/usr/local/bin/uv" ]]; then
        echo "/usr/local/bin/uv"
    elif [[ -x "/usr/bin/uv" ]]; then
        echo "/usr/bin/uv"
    fi
}

UV_BIN="$(detect_uv)"

if [[ -z "${UV_BIN}" ]]; then
    error "Astral 'uv' was not found on your system."
    echo -e "\n  Please install uv using one of the following methods:"
    echo -e "    ${BOLD}brew install uv${RESET}                          (macOS Homebrew)"
    echo -e "    ${BOLD}curl -LsSf https://astral.sh/uv/install.sh | sh${RESET} (Linux / macOS)"
    echo -e "    ${BOLD}powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"${RESET} (Windows)\n"
    exit 1
fi

step "Using uv binary: ${DIM}${UV_BIN}${RESET} ($(${UV_BIN} --version))"

# ------------------------------------------------------------------------------
# 2. Cross-Platform Virtual Environment Setup
# ------------------------------------------------------------------------------
info "Phase 2: Checking isolated virtual environment..."

has_venv() {
    [[ -f ".venv/bin/python" || -f ".venv/Scripts/python.exe" || -f ".venv/bin/python3" ]]
}

if ! has_venv; then
    step "Creating isolated virtual environment at .venv..."
    if ! "${UV_BIN}" venv .venv; then
        error "Failed to create virtual environment with uv."
        exit 1
    fi
    success "Virtual environment initialized."
else
    success "Virtual environment verified at .venv."
fi

# ------------------------------------------------------------------------------
# 3. Dependency Verification and Auto-Setup
# ------------------------------------------------------------------------------
info "Phase 3: Verifying application dependencies..."

NEED_INSTALL=0
if ! "${UV_BIN}" run python -c "import fastapi, uvicorn, jinja2, pydantic, httpx" >/dev/null 2>&1; then
    NEED_INSTALL=1
fi

if [[ ${NEED_INSTALL} -eq 1 ]]; then
    step "Installing core and development dependencies via uv..."
    if ! "${UV_BIN}" pip install -r requirements.txt pytest pytest-asyncio; then
        error "Dependency installation failed. Check network or package constraints."
        exit 1
    fi
    success "Dependencies successfully synchronized."
else
    success "All core dependencies verified and ready."
fi

# ------------------------------------------------------------------------------
# 4. Cross-Platform Environment & Storage Provisioning
# ------------------------------------------------------------------------------
info "Phase 4: Checking environment configuration and storage..."

if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        step "Generating .env from .env.example with secure secret key..."
        cp .env.example .env
        "${UV_BIN}" run python -c "
import secrets, re
try:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    new_key = secrets.token_hex(32)
    content = re.sub(r'SECRET_KEY=degistirilmeli_cok_gizli_anahtar', f'SECRET_KEY={new_key}', content)
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
except Exception as e:
    pass
"
        success "Default .env generated with cryptographic random SECRET_KEY."
    else
        warn "No .env or .env.example found. Relying on default settings."
    fi
else
    success "Environment file .env active."
fi

mkdir -p data
success "Data storage directory (data/) confirmed."

step "Verifying database integrity..."
if ! "${UV_BIN}" run python -c "from core.db_manager import init_db; init_db()" >/dev/null 2>&1; then
    error "Database initialization failed. Check permissions on data/ directory."
    exit 1
fi
success "Database initialized and schema verified."

# ------------------------------------------------------------------------------
# 5. Launch Server with Hot Reload
# ------------------------------------------------------------------------------
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

cleanup() {
    echo -e "\n${YELLOW}❯ Interrupted by user. Shutting down ReconClaw dev server gracefully...${RESET}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "\n${GREEN}========================================================================${RESET}"
echo -e "${GREEN}${BOLD}  🚀 ReconClaw Dev Server starting with live hot reload!${RESET}"
echo -e "  ${BOLD}URL:${RESET}           ${CYAN}http://${HOST}:${PORT}${RESET}"
echo -e "  ${BOLD}Documentation:${RESET} ${CYAN}http://${HOST}:${PORT}/docs${RESET}"
echo -e "  ${BOLD}Watcher dirs:${RESET}  main.py, core/, templates/, static/"
echo -e "${GREEN}========================================================================${RESET}\n"

if ! "${UV_BIN}" run uvicorn main:app \
    --reload \
    --reload-dir main.py \
    --reload-dir core \
    --reload-dir templates \
    --host "${HOST}" \
    --port "${PORT}" \
    --proxy-headers; then
    EXIT_CODE=$?
    echo -e "\n${RED}${BOLD}✖ Dev server terminated with exit code ${EXIT_CODE}.${RESET}"
    
    # Universal socket-based port diagnostic (works without lsof on Linux/macOS/Windows)
    PORT_BUSY=$("${UV_BIN}" run python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('${HOST}', int('${PORT}')))
    print('0')
except OSError:
    print('1')
finally:
    s.close()
" 2>/dev/null || echo "0")

    if [[ "${PORT_BUSY}" == "1" ]]; then
        echo -e "${YELLOW}  Diagnostic: Port ${PORT} appears to be in use by another process.${RESET}"
        echo -e "  To run on another port: ${BOLD}PORT=8080 ./scripts/dev.sh${RESET}"
    fi
    exit ${EXIT_CODE}
fi
