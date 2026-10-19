# DevOps and Environment Management

ReconClaw runs locally under Uvicorn or in production as Docker Compose behind Caddy. Settings come from environment variables.

The infrastructure combines Python 3.12 slim images, Caddy reverse proxying, automated HTTPS certificates, and single-file SQLite database persistence.

## Environment matrix

Two environments exist in the repository. There is no staging configuration.

- **Local**: `./scripts/dev.sh` (Linux/macOS) or `.\scripts\dev.ps1` (Windows) on `http://127.0.0.1:8000`. `ALLOW_PRIVATE_TARGETS` defaults to true so lab hosts can be scanned.
- **Production**: [[docker-compose.yml]] with Caddy and a Cloudflare origin certificate. Set `ALLOW_PRIVATE_TARGETS=false` on any internet-facing server.

## Containerization architecture

Application containerization enforces privilege separation and minimal image attack surfaces.

The [[Dockerfile]] builds upon `python:3.12-slim`, executes under a non-root system user (`reconclaw`), and defines an automated container healthcheck against the `/api/health` endpoint.

## Reverse proxy and HTTPS automation

Web traffic routing and TLS termination are managed by Caddy.

Defined in [[docker-compose.yml]] and [[deploy/Caddyfile]], Caddy provides automatic HTTP-to-HTTPS redirection, zstd and gzip compression, and reverse proxy forwarding to the FastAPI application with proxy header preservation.

## Configuration and secrets management

All operational behaviors adapt dynamically based on environment variables.

Configuration loaded via `core/config.py` prioritizes real environment variables over `.env` files. Critical security flags include `PUBLIC_URL`, `COOKIE_SECURE`, and `ALLOW_PRIVATE_TARGETS`.

## Persistence

The SQLite file lives on a Docker volume so it survives container rebuilds.

The path comes from `RECONCLAW_DB` and resolves to the `reconclaw-data` volume in [[docker-compose.yml]]. No backup job exists in the repository.
