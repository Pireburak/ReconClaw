# Classified Entity Model

ReconClaw organizes security assessments, user operations, and attack surface tracking around structured domain entities.

Every entity maintains explicit schema definitions, validation invariants, and relational lifecycles across SQLite tables and runtime data structures.

## User identity and access entities

User identity models govern credentials, roles, and federated authentication providers.

The `User` record stored in the `users` table tracks authentication status, role permissions (owner, admin, moderator, user), and quota limits. The `Identity` record in the `identities` table links external OAuth subjects from Google, GitHub, Microsoft, and Apple to an internal user identifier.

### Session and token entities

Session states govern web browser authentication and API client access tokens.

The `Session` entity stored in `sessions` maps a SHA-256 hashed session token to a user with an absolute expiration date. API access relies on unique static bearer tokens managed directly on user rows.

## Scan and reconnaissance entities

Scan entities capture point-in-time snapshots of an attack surface and port exposures.

A `Scan` entity represents a completed reconnaissance execution against a normalized target host. It records IP resolution, scan duration, aggregated risk score, risk level, and the complete serialized JSON report.

### Open port entity

The `OpenPort` entity represents an actively responsive TCP port on a target host.

Defined in `open_ports`, this entity stores the port number, protocol, detected service name, extracted banner text, and an individual risk weight determined by [[core/engine.py#SERVICE_MAP]].

### Finding entity

The `Finding` entity captures specific vulnerability insights produced by inspection plugins.

Stored in `findings`, each finding links to an originating scan and includes the inspecting plugin name (e.g. `http_headers`, `tls_cert`), target port, severity level, title, and descriptive technical details.

## Threat intelligence entities

Intelligence entities evaluate exposures against structured cybersecurity frameworks and metrics.

These entities provide deterministic calculations that structure raw findings into actionable risk models without relying on nondeterministic LLM generation.

### Security scorecard entity

The `Scorecard` entity models an objective evaluation of defensive posture graded from A+ to F.

Computed by [[core/intel.py#scorecard]], it aggregates five categories: network exposure, patch level, encryption quality, web hardening, and information disclosure. Severe vulnerabilities enforce strict grade ceilings.

### MITRE ATT and CK entity

The `AttackMapping` entity aligns discovered services with adversary tactics and techniques.

Defined in [[core/intel.py#attack_mapping]], it maps exposed services to standardized ATT&CK techniques in [[core/intel.py#TECHNIQUES]], constructing an end-to-end cyber kill chain from initial access to operational impact.

### Compliance control entity

The `ComplianceControl` entity models automated regulatory checks for information security standards.

Computed by [[core/intel.py#compliance]], it maps findings against ISO/IEC 27001:2022 Annex A controls and Turkish KVKK Article 12 data security obligations, yielding pass, partial, or fail status.

## Continuous monitoring entities

Continuous monitoring entities drive autonomous task scheduling and surface change tracking.

These models allow users to define periodic recurring audits that compare historical scan state to produce alert notifications.

### Monitor task entity

The `Monitor` entity represents a scheduled recurring reconnaissance task for a target.

Managed by [[core/monitor.py#list_monitors]], it defines the target host, execution interval (hourly, daily, weekly), port limit, optional webhook endpoint, enabled state, and next scheduled execution timestamp.

### Alert event entity

The `Alert` entity records a security delta detected between consecutive reconnaissance scans.

Stored in `alerts` and classified by severity level, alerts capture events such as newly opened ports, novel CVE signatures, changed service banners, resolved vulnerabilities, or significant risk score variance.
