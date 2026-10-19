#!/usr/bin/env bash
# ==============================================================================
# ReconClaw Test Runner
# Features:
#   - Automated uv detection and test dependency verification
#   - Pytest execution with progress reporting and timing
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

UV_BIN=""
if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
elif [[ -x "/opt/homebrew/bin/uv" ]]; then
    UV_BIN="/opt/homebrew/bin/uv"
elif [[ -x "$HOME/.cargo/bin/uv" ]]; then
    UV_BIN="$HOME/.cargo/bin/uv"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
    UV_BIN="$HOME/.local/bin/uv"
fi

if [[ -z "${UV_BIN}" ]]; then
    error "Astral 'uv' is required to run test suite."
    exit 1
fi

if [[ ! -d ".venv" || ! -f ".venv/bin/python" ]]; then
    step "Initializing isolated test virtualenv at .venv..."
    "${UV_BIN}" venv .venv
fi

# Ensure pytest is installed
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
