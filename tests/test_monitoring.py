import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import monitor, recon  # noqa: E402
from core.engine import ScanResult  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "monitor.db"))
    import main

    with TestClient(main.app) as c:
        c.post("/auth/register", json={"email": "izle@example.com", "password": "parola123"})
        yield c


def open_ports(*ports):
    async def fake_run(self):
        return ScanResult(self.target, self.ip, [{"port": p, "protocol": "TCP", "banner": ""} for p in ports], 0.01)
    return fake_run


def new_monitor(client, **extra):
    return client.post("/api/monitors", json={"target": "127.0.0.1", "interval": "daily", "max_port": 50, **extra})


# ---------------------------------------------------------------- izleme
def test_monitoring_requires_paid_plan_and_respects_limits(client):
    assert new_monitor(client).status_code == 402
    client.post("/api/billing/checkout", json={"plan": "pro"})
    assert new_monitor(client, interval="hourly").status_code == 402  # saatlik: Ultra+
    assert new_monitor(client, max_port=5000).status_code == 402      # Pro port sınırı 1024
    created = new_monitor(client).json()
    assert created["target"] == "127.0.0.1" and created["interval_label"] == "Günlük" and created["enabled"]
    assert new_monitor(client, target="localhost").status_code == 402  # Pro: 1 görev
    data = client.get("/api/monitors").json()
    assert data["limit"] == 1 and len(data["monitors"]) == 1


def test_monitor_detects_new_open_port_and_sends_webhook(client, monkeypatch):
    import main

    sent = []

    async def fake_webhook(url, target, items, scan_id=None):
        sent.append((url, [a["title"] for a in items]))

    monkeypatch.setattr(monitor, "send_webhook", fake_webhook)
    client.post("/api/billing/checkout", json={"plan": "ultra"})
    mid = new_monitor(client, webhook="https://hooks.example.com/abc").json()["id"]
    assert client.get("/api/monitors").json()["monitors"][0]["webhook"] == "https://hooks.example.com/…"

    monkeypatch.setattr(main.AsyncScanner, "run", open_ports(80))
    first = client.post(f"/api/monitors/{mid}/run").json()
    assert [a["title"] for a in first["alerts"]] == ["İzleme başladı"]
    assert sent == []  # başlangıç taraması bildirim göndermez

    monkeypatch.setattr(main.AsyncScanner, "run", open_ports(80, 3306))
    second = client.post(f"/api/monitors/{mid}/run").json()
    assert second["alerts"][0]["level"] == "critical"
    assert second["alerts"][0]["title"] == "Yeni açık port: 3306/MySQL"
    assert sent and sent[0][0] == "https://hooks.example.com/abc"

    alerts = client.get("/api/alerts").json()
    assert alerts["unseen"] >= 2
    client.post("/api/alerts/seen")
    assert client.get("/api/alerts").json()["unseen"] == 0

    row = client.get("/api/monitors").json()["monitors"][0]
    assert row["last_status"].startswith("2 önemli") or row["last_status"].endswith("önemli değişiklik")
    assert row["next_run"] > row["last_run"]


def test_monitor_pauses_after_downgrade(client):
    client.post("/api/billing/checkout", json={"plan": "pro"})
    mid = new_monitor(client).json()["id"]
    client.post("/api/billing/cancel")
    row = monitor.get_monitor(client.get("/api/me").json()["id"], mid)
    import asyncio
    import main

    result = asyncio.run(monitor.run_monitor(row, main.run_scan))
    assert "duraklatıldı" in result["status"]
    assert client.get("/api/monitors").json()["monitors"][0]["enabled"] is False


def test_scheduler_picks_due_monitors(client):
    client.post("/api/billing/checkout", json={"plan": "pro"})
    mid = new_monitor(client).json()["id"]
    assert [r["id"] for r in monitor.due_monitors()] == [mid]
    client.patch(f"/api/monitors/{mid}", json={"enabled": False})
    assert monitor.due_monitors() == []
    assert client.delete(f"/api/monitors/{mid}").status_code == 200


def test_change_alerts_rules():
    base = {"scan_id": 1, "target": "t", "scan_time": "x", "overall_risk": 10, "risk_level": {}, "total_open": 1,
            "analysis": [{"port": 22, "service": "SSH", "banner": "OpenSSH_8.9"}], "findings": [], "cve_alerts": []}
    new = {**base, "scan_id": 2, "overall_risk": 40, "total_open": 1,
           "analysis": [{"port": 22, "service": "SSH", "banner": "OpenSSH_9.6"}], "cve_alerts": ["[Port 22] eski"]}
    titles = [(a["level"], a["title"]) for a in monitor.change_alerts(base, new)]
    assert titles[0] == ("critical", "Yeni zafiyet imzası")
    assert ("medium", "Servis sürümü değişti: 22/SSH") in titles
    assert ("high", "Risk skoru arttı: 10 → 40") in titles
    assert monitor.change_alerts(base, base) == []


def test_webhook_validation():
    assert monitor.validate_webhook("") is None
    with pytest.raises(monitor.MonitorError):
        monitor.validate_webhook("ftp://ornek.com/x")


# ---------------------------------------------------------------- pasif keşif
def test_email_security_rules():
    strict = recon.email_security({"MX": ["10 mx.ornek.com."], "TXT": ["v=spf1 include:_spf.x.com -all"],
                                   "DMARC": ["v=DMARC1; p=reject"], "CAA": ["0 issue letsencrypt.org"]})
    assert strict["score"] == 100 and strict["spf"] == "katı" and strict["dmarc"] == "reject"
    weak = recon.email_security({"MX": ["10 mx.ornek.com."], "TXT": [], "DMARC": [], "CAA": []})
    assert {f["title"] for f in weak["findings"]} == {"SPF kaydı yok", "DMARC kaydı yok", "CAA kaydı yok"}
    assert weak["score"] == 50
    open_spf = recon.email_security({"MX": [], "TXT": ["v=spf1 +all"], "DMARC": ["v=DMARC1; sp=reject; p=none"], "CAA": ["x"]})
    assert open_spf["spf"] == "tehlikeli" and open_spf["dmarc"] == "none"


def test_subdomain_tags_and_cleaning():
    assert recon.tags_for("admin.ornek.com", "ornek.com") == ["yönetim"]
    assert set(recon.tags_for("vpn-dev.ornek.com", "ornek.com")) == {"geliştirme", "uzak erişim"}
    assert recon.tags_for("www.ornek.com", "ornek.com") == []
    names = recon._clean_names(["*.ornek.com\nmail.ornek.com", "kotu.com", "API.Ornek.com"], "ornek.com")
    assert names == ["ornek.com", "api.ornek.com", "mail.ornek.com"]
    with pytest.raises(recon.ReconError):
        recon.normalize_domain("10.0.0.1")


def test_recon_endpoint(client, monkeypatch):
    async def fake_names(client_, domain):
        return [f"admin.{domain}", f"www.{domain}"], "crt.sh"

    async def fake_dns(client_, domain):
        return {"A": ["93.184.215.14"], "AAAA": [], "MX": [], "NS": ["ns1."], "TXT": [], "CAA": [], "DMARC": []}

    async def fake_resolve(name, sem):
        return [] if name.startswith("admin.") else ["93.184.215.14"]

    monkeypatch.setattr(recon, "certificate_names", fake_names)
    monkeypatch.setattr(recon, "dns_records", fake_dns)
    monkeypatch.setattr(recon, "_resolve", fake_resolve)

    assert client.post("/api/recon", json={"domain": "ornek.com"}).status_code == 402
    client.post("/api/billing/checkout", json={"plan": "pro"})
    data = client.post("/api/recon", json={"domain": "https://Ornek.com/yol"}).json()
    assert data["domain"] == "ornek.com" and data["source"] == "crt.sh"
    assert data["summary"] == {"subdomains": 3, "alive": 2, "interesting": 1, "unique_ips": 1}
    assert data["subdomains"][0]["name"] == "ornek.com"
    history = client.get("/api/recon").json()
    assert history[0]["domain"] == "ornek.com"
    assert client.get(f"/api/recon/{data['id']}").json()["summary"]["alive"] == 2
    assert client.post("/api/recon", json={"domain": "192.168.1.1"}).status_code == 400
