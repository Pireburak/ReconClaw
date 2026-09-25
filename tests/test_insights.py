from core.insights import build_stats, compare_reports


def report(scan_id, target, ports, score, cves=(), findings=(), time="2026-09-25 10:00:00"):
    level = "critical" if score > 75 else "high" if score > 50 else "medium" if score > 25 else "low"
    return {
        "scan_id": scan_id, "target": target, "resolved_ip": "1.1.1.1", "scan_time": time,
        "overall_risk": score, "risk_level": {"key": level, "label": level},
        "total_open": len(ports), "cve_alerts": list(cves), "findings": list(findings),
        "analysis": [{"port": p, "service": f"svc{p}", "banner": b, "protocol": "TCP", "risk": 10} for p, b in ports],
    }


def finding(port, severity, title):
    return {"plugin": "http_headers", "port": port, "severity": severity, "title": title, "detail": ""}


def test_stats_use_latest_scan_per_target():
    reports = [
        report(1, "a.com", [(22, ""), (80, "")], 80, cves=["[Port 22] eski"]),
        report(2, "b.com", [(443, "")], 10, findings=[finding(443, "medium", "HSTS yok")]),
        report(3, "a.com", [(80, "")], 30),
    ]
    s = build_stats(reports)
    assert s["total_scans"] == 3 and s["domains_scanned"] == 2
    assert s["severity"] == {"critical": 0, "high": 0, "medium": 1, "low": 0}
    assert s["vulnerabilities"] == 1
    assert s["high_risk_targets"] == 0
    assert s["avg_risk"] == 20
    assert [t["target"] for t in s["targets"]] == ["a.com", "b.com"]
    assert len(s["trend"]) == 3
    assert s["events"][0]["scan_id"] == 3  # en yeni olay en üstte
    assert any(e["level"] == "critical" for e in s["events"])


def test_empty_stats():
    s = build_stats([])
    assert s["domains_scanned"] == 0 and s["posture"] is None and s["events"] == []


def test_compare_reports():
    old = report(1, "a.com", [(22, "OpenSSH_5.3"), (80, "nginx"), (21, "")], 90,
                 cves=["[Port 22] eski"], findings=[finding(80, "low", "CSP yok")])
    new = report(2, "a.com", [(22, "OpenSSH_9.6"), (80, "nginx"), (443, "")], 20,
                 findings=[finding(443, "medium", "HSTS yok")])
    d = compare_reports(old, new)
    assert d["risk_delta"] == -70
    assert [p["port"] for p in d["opened"]] == [443]
    assert [p["port"] for p in d["closed"]] == [21]
    assert d["changed"] == [{"port": 22, "service": "svc22", "old_banner": "OpenSSH_5.3", "new_banner": "OpenSSH_9.6"}]
    assert d["unchanged"] == 1
    assert d["resolved_cves"] == ["[Port 22] eski"] and d["new_cves"] == []
    assert [f["title"] for f in d["new_findings"]] == ["HSTS yok"]
    assert [f["title"] for f in d["resolved_findings"]] == ["CSP yok"]
