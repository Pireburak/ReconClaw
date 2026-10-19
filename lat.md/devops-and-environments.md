# DevOps and Environment Management

ReconClaw utilizes containerized deployment workflows and strict environment segregation across development, staging, and production tiers.

The infrastructure combines Python 3.12 slim images, Caddy reverse proxying, automated HTTPS certificates, and single-file SQLite database persistence.

## Environment matrix

ReconClaw supports three distinct operating environments configured via environment variables.

- **Local Development**: Runs directly via Uvicorn on `http://127.0.0.1:8000` with internal address scanning permitted for local lab testing.
- **Staging Tier**: Isolated container instance validating migrations, OAuth callbacks, and continuous monitoring tasks against staging targets.
- **Live Production**: Hardened multi-container Docker Compose deployment fronted by Caddy with enforced TLS and private address restrictions.

## Containerization architecture

Application containerization enforces privilege separation and minimal image attack surfaces.

The [[Dockerfile]] builds upon `python:3.12-slim`, executes under a non-root system user (`reconclaw`), and defines an automated container healthcheck against the `/api/health` endpoint.

## Reverse proxy and HTTPS automation

Web traffic routing and TLS termination are managed by Caddy.

Defined in [[docker-compose.yml]] and [[deploy/Caddyfile]], Caddy provides automatic HTTP-to-HTTPS redirection, zstd and gzip compression, and reverse proxy forwarding to the FastAPI application with proxy header preservation.

## Configuration and secrets management

All operational behaviors adapt dynamically based on environment variables.

Configuration loaded via `core/config.py` prioritizes real environment variables over `.env` files. Critical security flags include `PUBLIC_URL`, `COOKIE_SECURE`, and `ALLOW_PRIVATE_TARGETS`.

## Persistence and backup procedures

Database persistence isolates runtime state inside dedicated container volumes.

The SQLite database file configured by `RECONCLAW_DB` resides on the `reconclaw-data` volume. Scheduled backup routines execute atomic SQLite backups via `.backup` or VACUUM operations into secure external storage.
