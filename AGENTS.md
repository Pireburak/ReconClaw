# AGENTS.md — ReconClaw Engineering & Knowledge Graph Rulebook

# Before starting work

Use Lat's knowledge graph to ground each task before changing code.

- Run `lat search "<query>"` to locate architectural concepts, entity models, and contracts relevant to your task.
- Run `lat locate "<Section Name>"` for direct concept inspection.
- Read referenced `lat.md/` sections to understand implemented constraints and design intent before writing or modifying code.

# Post-task checklist (REQUIRED — do not skip)

After EVERY task, before responding to the user:

- [ ] Update `lat.md/` if you added or changed meaningful implemented functionality, architecture, entities, tests, or behavior. Keep it a focused snapshot of the current implemented state, not a journal/changelog.
- [ ] Run `lat check` — all validations must pass with 0 errors.
- [ ] Do not skip these steps. Do not consider your task done until both are complete.

---

# Double-Layer Deterministic Pipeline & Anti-Hallucination Rules

ReconClaw enforces strict output determinism and grounding to eliminate AI hallucination:

1. **Layer 1: Deterministic Ground Truth (`core/intel.py`, `core/engine.py`)**
   - All security calculations (0–100 risk score, A+…F grade, ATT&CK mapping, ISO 27001/KVKK compliance) MUST remain deterministic and offline-capable.
   - Never replace mathematical scorecards or regex signature tables with speculative AI evaluations.
2. **Layer 2: Grounded Reasoning & Hallucination Limiter (`core/ai.py`)**
   - Telemetry fed to Claude MUST be bounded within explicit `<rapor_verisi>` XML blocks.
   - The model MUST NOT invent CVE identifiers, unverified open ports, or speculative service versions not present in the scan evidence.
   - Always maintain the deterministic fallback (`core/ai.py#offline`): if the LLM is unreachable or refuses, the offline engine must produce a verifiable remediation plan without interruption.

---

# DevOps & Live Task Tracking

- **Local Development**: `http://127.0.0.1:8000` via Uvicorn. Internal IP scanning enabled only when testing in local lab environments (`ALLOW_PRIVATE_TARGETS=true`).
- **Staging**: not implemented yet. Planned in `docs/PLAN.md` (Phase S). Do not describe it as existing in `lat.md/` until it is built.
- **Production / Live**: Multi-container Docker deployment (`docker-compose.yml`) behind Caddy with automated Cloudflare origin TLS.
- **Continuous Monitoring**: All recurring tasks run via `core/monitor.py#scheduler_loop` using atomic updates on SQLite without blocking the main event loop.
- **Delta Engine**: Always verify changes through `compare_reports` before generating alerts. Newly opened database or administrative ports are classified as `critical`.

---

# What is lat.md?

Lat.md is the project's structured knowledge graph for architecture, design decisions, behavior, and tests.

The graph lives in `lat.md/` as cross-linked Markdown describing **what** the project does and **why**. Use it to ground work in actual architecture, and keep it a focused snapshot of the current implemented state rather than a journal or changelog.

# Commands

Use these commands to navigate and validate the project knowledge graph.

```bash
lat locate "Section Name"      # find a section by name (exact, fuzzy)
lat refs "file#Section"        # find what references a section
lat search "natural language"  # semantic search across all sections
lat external show <handle>     # inspect a pinned external source before cloning it
lat check                      # run full graph and documentation validation
lat reindex                    # rebuild the embedding search index
```

# Syntax and Section Rules

- **Section IDs**: `lat.md/path/to/file#Heading#SubHeading` (full) or `file#Heading#SubHeading` (short).
- **Wiki Links**: `[[target]]` or `[[target|alias]]` pointing to files, sections, or source symbols (`[[core/engine.py#AsyncScanner]]`).
- **Leading Paragraph**: Every section MUST have a leading paragraph immediately after the heading, ≤250 characters (excluding `[[wiki link]]` content).
