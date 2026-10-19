# Continuous Tasks and Attack Surface Monitoring

ReconClaw incorporates autonomous background task tracking to monitor changes across network attack surfaces continuously.

The subsystem schedules recurring scans, computes state differentials against previous snapshots, classifies risk deltas, and dispatches real-time alerts.

## Scheduler architecture and task loop

The background task engine continuously polls the database for scheduled monitoring jobs.

The worker loop in [[core/monitor.py#scheduler_loop]] awakens at configured intervals to query [[core/monitor.py#due_monitors]]. Due jobs are dispatched sequentially, preventing connection flooding while updating next-run timestamps atomically.

### Dynamic concurrency and rate control

Reconnaissance workloads are throttled to ensure host stability and target compliance.

Each scanning task operates under an asyncio semaphore inside [[core/engine.py#AsyncScanner]]. In addition, user-specific rate limits and plan tiers from `plans` restrict scan frequency and port breadth.

## Delta differential engine

Surface comparison isolates actionable changes between sequential target scans.

Function [[core/insights.py#compare_reports]] examines the current scan against historical results. The delta calculation identifies opened ports, closed ports, altered service banners, novel CVE signatures, and risk score variances.

### Alert classification hierarchy

Detected changes are categorized into strict severity tiers based on risk exposure.

- **Critical**: new CVE signatures and newly opened critical ports.
- **High**: new high-severity plugin findings, or risk score up 10 or more.
- **Medium**: changed service banners and new medium-severity findings.
- **Info**: closed ports, resolved CVEs, risk score down 10 or more.

## Alert dispatching and webhook integration

Security alerts are persisted in the database and relayed to external operations channels.

Function [[core/monitor.py#send_webhook]] formats alert payloads into compatible schemas for Discord, Slack, and custom HTTP endpoints. Webhook URLs undergo strict scheme and host validation to prevent internal network abuse.

## Task status

Each monitor row keeps `last_run`, `next_run` and a free-text `last_status`; there is no separate job state machine.

[[core/monitor.py#run_monitor]] writes `last_status` (for example "Değişiklik yok" or "HATA: ...") and stores a failed scan as a medium alert.
