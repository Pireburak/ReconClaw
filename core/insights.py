"""
Kayıtlı tarama raporlarından dashboard istatistikleri ve iki tarama arasındaki farkı üretir.
Fonksiyonlar saf Python'dur (veritabanı / ağ erişimi yok), bu yüzden kolayca test edilir.
"""

from collections import Counter

from core.engine import risk_level

SEVERITY_KEYS = ("critical", "high", "medium", "low")


def _latest_per_target(reports):
    latest = {}
    for report in reports:  # eskiden yeniye sıralı; son gelen en güncel
        latest[report["target"]] = report
    return list(latest.values())


def _severity_counts(report) -> Counter:
    counts = Counter({key: 0 for key in SEVERITY_KEYS})
    counts["critical"] += len(report.get("cve_alerts", []))
    for finding in report.get("findings", []):
        if finding["severity"] in counts:
            counts[finding["severity"]] += 1
    return counts


def build_stats(reports: list) -> dict:
    """reports: kullanıcının tam raporları, eskiden yeniye."""
    current = _latest_per_target(reports)
    severity = Counter({key: 0 for key in SEVERITY_KEYS})
    for report in current:
        severity.update(_severity_counts(report))

    distribution = Counter({key: 0 for key in ("low", "medium", "high", "critical")})
    distribution.update(r["risk_level"]["key"] for r in current)
    port_counts = Counter(p["port"] for r in current for p in r["analysis"])
    services = {p["port"]: p["service"] for r in current for p in r["analysis"]}
    avg_risk = round(sum(r["overall_risk"] for r in current) / len(current)) if current else 0
    worst = max((r["overall_risk"] for r in current), default=0)

    events = []
    for report in reversed(reports[-15:]):
        base = {"target": report["target"], "time": report["scan_time"], "scan_id": report["scan_id"]}
        for alert in report.get("cve_alerts", []):
            events.append({**base, "level": "critical", "text": alert})
        for f in report.get("findings", []):
            if f["severity"] in ("high", "medium"):
                events.append({**base, "level": f["severity"], "text": f"[Port {f['port']}] {f['title']}"})
        events.append({**base, "level": report["risk_level"]["key"], "kind": "scan",
                       "text": f"Tarama tamamlandı: {report['total_open']} açık port, risk %{report['overall_risk']}"})

    return {
        "total_scans": len(reports),
        "domains_scanned": len(current),
        "open_ports": sum(r["total_open"] for r in current),
        "vulnerabilities": sum(severity.values()),
        "severity": dict(severity),
        "high_risk_targets": distribution["high"] + distribution["critical"],
        "risk_distribution": dict(distribution),
        "avg_risk": avg_risk,
        "posture": risk_level(worst) if current else None,
        "trend": [
            {"scan_id": r["scan_id"], "time": r["scan_time"], "target": r["target"],
             "score": r["overall_risk"], "open": r["total_open"],
             "vulns": sum(_severity_counts(r).values())}
            for r in reports[-20:]
        ],
        "top_ports": [
            {"port": port, "service": services[port], "count": count}
            for port, count in port_counts.most_common(8)
        ],
        "targets": [
            {"target": r["target"], "ip": r["resolved_ip"], "score": r["overall_risk"],
             "level": r["risk_level"], "open": r["total_open"], "scan_id": r["scan_id"], "time": r["scan_time"]}
            for r in sorted(current, key=lambda r: r["overall_risk"], reverse=True)
        ],
        "events": events[:40],
    }


def compare_reports(old: dict, new: dict) -> dict:
    """İki tarama raporu arasındaki farkı döndürür (old -> new)."""
    old_ports = {p["port"]: p for p in old["analysis"]}
    new_ports = {p["port"]: p for p in new["analysis"]}

    changed = [
        {"port": port, "service": new_ports[port]["service"],
         "old_banner": old_ports[port]["banner"], "new_banner": new_ports[port]["banner"]}
        for port in sorted(old_ports.keys() & new_ports.keys())
        if old_ports[port]["banner"] != new_ports[port]["banner"]
    ]

    def finding_key(f):
        return (f["plugin"], f["port"], f["title"])

    old_findings = {finding_key(f): f for f in old.get("findings", [])}
    new_findings = {finding_key(f): f for f in new.get("findings", [])}
    old_cves, new_cves = set(old.get("cve_alerts", [])), set(new.get("cve_alerts", []))

    return {
        "old": {k: old[k] for k in ("scan_id", "target", "scan_time", "overall_risk", "risk_level", "total_open")},
        "new": {k: new[k] for k in ("scan_id", "target", "scan_time", "overall_risk", "risk_level", "total_open")},
        "same_target": old["target"] == new["target"],
        "risk_delta": new["overall_risk"] - old["overall_risk"],
        "opened": [new_ports[p] for p in sorted(new_ports.keys() - old_ports.keys())],
        "closed": [old_ports[p] for p in sorted(old_ports.keys() - new_ports.keys())],
        "changed": changed,
        "unchanged": len(old_ports.keys() & new_ports.keys()) - len(changed),
        "new_findings": [new_findings[k] for k in sorted(new_findings.keys() - old_findings.keys())],
        "resolved_findings": [old_findings[k] for k in sorted(old_findings.keys() - new_findings.keys())],
        "new_cves": sorted(new_cves - old_cves),
        "resolved_cves": sorted(old_cves - new_cves),
    }
