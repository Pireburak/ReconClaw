---
meta:
  contentType: Reference
---
# ReconClaw Knowledge Graph

ReconClaw is an asynchronous attack surface management, port reconnaissance, and AI-assisted security analysis engine.

This knowledge graph anchors source code to domain concepts, architectural invariants, threat models, and operational runbooks. It serves as the single source of truth for engineering and agentic workflows.

## Execution commands

Essential operational commands for local development, test validation, container builds, and graph checks.

### Run development server

Start the local FastAPI application with uv, dependency sync, and hot reload across Linux, macOS, and Windows.

```bash
# Linux / macOS / Git Bash / WSL
./scripts/dev.sh

# Windows PowerShell
.\scripts\dev.ps1

# Makefile (Linux / macOS)
make dev
```

### Build and verify project

Execute multi-phase bytecode compilation, module import verification, and database schema sanity tests.

```bash
# Linux / macOS / Git Bash / WSL
./scripts/build.sh

# Windows PowerShell
.\scripts\build.ps1

# Makefile (Linux / macOS)
make build
```

### Run test suite

Execute the automated test suite across network engines, analyzers, and security checks using uv.

```bash
# Linux / macOS / Git Bash / WSL
./scripts/test.sh

# Windows PowerShell
.\scripts\test.ps1

# Makefile (Linux / macOS)
make test
```

### Build and deploy containers

Spin up the containerized deployment fronted by Caddy reverse proxy with automated TLS.

```bash
docker compose up -d --build
```

### Operational management CLI

Execute administrative user role provisioning and account maintenance routines.

```bash
python manage.py list-admins
python manage.py make-admin <email>
```

### Knowledge graph operations

Validate documentation cross-references, update semantic search vectors, and serve the web UI.

```bash
lat check
lat reindex
lat ui
```

## Navigation and domain indices

Select the domain guide matching your active task to understand implemented architecture, constraints, and source locations.

- [[entities]] — Domain entities, relational models, state machines, and relational integrity constraints.
- [[deterministic-engine]] — Double-layer verified deterministic pipeline, rule engines, and hallucination limiter.
- [[tasks-and-monitoring]] — Continuous attack surface monitoring (ASM), task queues, delta engines, and webhook alerts.
- [[devops-and-environments]] — Local and production setup, Docker, Caddy, and configuration.
- [[security-and-safety]] — SSRF prevention, target ownership verification, rate limits, and audit logging.
- [[architecture]] — High-level system architecture, FastAPI request pipeline, SQLite persistence, and concurrency model.
- [[tests]] — Verification test suite specifications and coverage matrices.

## System overview

Core technology stack, security boundaries, and architectural principles governing ReconClaw v9.0 Cortex.

- **Asynchronous Foundation**: Built on Python 3.10+, FastAPI, and asyncio with semaphores limiting network socket exhaustion ([[core/engine.py#AsyncScanner]]).
- **Deterministic First**: Every calculation (risk scores, MITRE ATT&CK techniques, ISO 27001/KVKK compliance) is computed deterministically before reaching any LLM ([[core/intel.py#analyze]]).
- **Hallucination Limiter**: Anthropic Claude outputs are bounded by strict XML schemas, system barriers, and offline deterministic fallback mechanisms ([[core/ai.py#analyze]]).
- **Continuous Monitoring**: Autonomous background task scheduler detects delta shifts across port banners, risk scores, and CVE signatures ([[core/monitor.py#scheduler_loop]]).
- **Single-Host Resilience**: Self-contained SQLite with foreign keys and no external database ([[core/db_manager.py#init_db]]).
