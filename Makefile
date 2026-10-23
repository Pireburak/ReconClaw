.PHONY: dev build test check clean help

help:
	@echo "ReconClaw Management Targets:"
	@echo "  make dev      - Run local development server with uv and hot reload"
	@echo "  make build    - Run multi-phase bytecode and schema integrity verification"
	@echo "  make test     - Execute automated pytest test suite"
	@echo "  make check    - Validate lat.md knowledge graph cross-references"
	@echo "  make clean    - Remove build artifacts and bytecode caches"

dev:
	@./scripts/dev.sh

build:
	@./scripts/build.sh

test:
	@./scripts/test.sh

check:
	@lat check

clean:
	@rm -rf __pycache__ core/__pycache__ tests/__pycache__ .pytest_cache
	@find . -type f -name "*.pyc" -delete
	@echo "Cleaned cache and bytecode artifacts."
