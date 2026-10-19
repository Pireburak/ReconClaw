# System Architecture

ReconClaw v9.0 Cortex is an asynchronous modular reconnaissance and threat modeling platform designed for high-concurrency scans.

It processes network targets from user inputs through asynchronous TCP connection routines, rule-based security analyzers, offline and online threat intelligence layers, and reactive event notifications.

## System topology

The architecture consists of a client layer, a web runtime, an asynchronous engine, and a SQLite persistence layer.

Incoming requests arrive at the FastAPI application [[main.py#app]], which handles routing, authentication, session validation, and JSON API serialization. The runtime interacts with [[core/engine.py#AsyncScanner]] to execute non-blocking network probes and delegates intelligence scoring to [[core/intel.py#analyze]].

## Network reconnaissance engine

The scanning engine conducts concurrent TCP connect operations bounded by concurrency limits.

Target strings are validated and normalized by [[core/engine.py#normalize_target]] to eliminate URL prefixes and trailing paths. [[core/engine.py#AsyncScanner]] queries DNS records, allocates an asyncio semaphore to protect local file descriptors, and dispatches socket probes against specified ports. Open ports receive banner extraction routines that query server response headers.

## Data storage architecture

Persistence is managed by a single-file SQLite database with strict foreign keys and transactional guarantees.

All database access passes through [[core/db_manager.py#get_db_connection]] and schema initialization is handled by [[core/db_manager.py#init_db]]. Scans, findings, user credentials, identity links, and scheduled monitors are stored relationally, allowing atomic writes and cascades.

## Threat intelligence and analytics pipeline

Intelligence extraction transforms raw open port banners into actionable security assessments.

The engine runs [[core/intel.py#scorecard]] to compute a 0–100 numerical score and A+–F letter grade, categorizes exposure using [[core/intel.py#attack_mapping]] into the MITRE ATT&CK matrix, and evaluates regulatory posture via [[core/intel.py#compliance]].
