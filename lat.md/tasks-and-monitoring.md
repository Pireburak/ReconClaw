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

Function `compare_reports` in `core/insights.py` examines the current scan against historical results. The delta calculation identifies opened ports, closed ports, altered service banners, novel CVE signatures, and risk score variances.

### Alert classification hierarchy

Detected changes are categorized into strict severity tiers based on risk exposure.

- **Critical**: Newly detected CVE signatures or exposure of critical database and remote access ports.
- **High**: New high-severity plugin findings or risk score increases of 10 or more points.
- **Medium**: Service version banner modifications or medium-severity configuration findings.
- **Low**: Minor configuration observations or low-impact findings.
- **Info**: Ports safely closed, CVEs remediated, or risk score reductions.

## Alert dispatching and webhook integration

Security alerts are persisted in the database and relayed to external operations channels.

Function [[core/monitor.py#send_webhook]] formats alert payloads into compatible schemas for Discord, Slack, and custom HTTP endpoints. Webhook URLs undergo strict scheme and host validation to prevent internal network abuse.

## Live and staging task tracking

Task tracking guarantees visibility into background jobs across environments.

Operators can monitor job states (`scheduled`, `running`, `completed`, `error`, `skipped`), review failure traces in the audit log, and trigger on-demand runs via [[core/monitor.py#run_monitor]].
