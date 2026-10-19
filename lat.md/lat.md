---
meta:
  contentType: Reference
---
# ReconClaw Knowledge Graph

ReconClaw is an asynchronous attack surface management, port reconnaissance, and AI-assisted security analysis engine.

This knowledge graph anchors source code to domain concepts, architectural invariants, threat models, and operational runbooks. It serves as the single source of truth for engineering and agentic workflows.

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
