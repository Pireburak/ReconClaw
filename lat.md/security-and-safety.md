# Security and Safety Controls

ReconClaw enforces defensive safety controls to prevent unauthorized network scanning, address abuse, and credential compromise.

These boundaries guarantee compliance with legal statutes, protect private corporate networks from SSRF attacks, and maintain non-repudiation across all operations.

## Target authorization and ownership verification

Target verification ensures operators only scan infrastructure they legitimately control.

When verification is enforced, [[core/verify.py#ensure_allowed]] requires domain ownership verification via DNS TXT records or HTTP token files hosted at `/.well-known/reconclaw-verify.txt`. Public test environments like `scanme.nmap.org` are maintained as allowed test targets.

## SSRF and internal network isolation

ReconClaw blocks unauthorized scanning of private subnets and local host loopbacks.

When `ALLOW_PRIVATE_TARGETS` is set to false in `core/config.py`, the scanner checks resolved IP addresses against IPv4 and IPv6 private, loopback, link-local, and multicast ranges, throwing validation errors on internal addresses.

## Rate limiting and quota management

Concurrency and request frequency limits prevent network congestion and denial-of-service conditions.

Per-user scanning quotas are enforced via `core/plans.py` based on active subscription tiers. In addition, global scan rate limits defined in `core/config.py` protect the host machine from excessive socket resource depletion.

## Authentication and credential hardening

User identities, passwords, and API credentials follow strict defensive cryptography standards.

Passwords are hashed using salted PBKDF2/SHA256, sessions use high-entropy random tokens stored as SHA-256 digests in SQLite, and session cookies enforce `HttpOnly`, `SameSite`, and `Secure` attributes in production.

## Audit logging and compliance accountability

Security-critical operations are recorded in an append-only audit trail for non-repudiation.

Function [[core/audit.py#log]] records user authentication attempts, permission changes, target additions, and administrative interventions alongside source IP addresses and timestamps, supporting ISO/IEC 27001 audit requirements.

## Legal compliance and ethical boundaries

Platform use is restricted to authorized vulnerability analysis and educational assessments.

ReconClaw explicitly warns operators regarding Turkish Criminal Code (TCK) Articles 243–245 prohibiting unauthorized computer access. The engine strictly restricts output to defensive remediation guidance.
