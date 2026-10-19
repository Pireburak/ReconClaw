#!/usr/bin/env bash
# ==============================================================================
# ReconClaw Test Runner (Cross-Platform: Linux / macOS / Windows)
# Features:
#   - Automated uv detection across Linux, macOS, and Windows
#   - Cross-platform virtual environment detection (.venv/bin or .venv/Scripts)
#   - Pytest execution with progress reporting and execution timing
# ==============================================================================

set -eo pipefail

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
error()   { echo -e "  ${RED}✖${RESET} ${RED}$1${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

export UV_LINK_MODE=copy

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
    error "Astral 'uv' is required to run test suite."
    exit 1
fi

has_venv() {
    [[ -f ".venv/bin/python" || -f ".venv/Scripts/python.exe" || -f ".venv/bin/python3" ]]
}

if ! has_venv; then
    step "Initializing isolated test virtualenv at .venv..."
    "${UV_BIN}" venv .venv
fi

if ! "${UV_BIN}" run python -c "import pytest, pytest_asyncio" >/dev/null 2>&1; then
    step "Installing test dependencies (pytest, pytest-asyncio)..."
    "${UV_BIN}" pip install -r requirements.txt pytest pytest-asyncio >/dev/null 2>&1
fi

echo -e "${PURPLE}${BOLD}❯ Running ReconClaw Test Suite with uv...${RESET}\n"

START_TIME=$(date +%s)

if "${UV_BIN}" run pytest -v "$@"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo -e "\n${GREEN}✔ All tests passed successfully in ${DURATION}s.${RESET}\n"
else
    EXIT_CODE=$?
    echo -e "\n${RED}✖ Test suite failed with exit code ${EXIT_CODE}.${RESET}\n"
    exit ${EXIT_CODE}
fi
