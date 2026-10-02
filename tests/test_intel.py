import asyncio

import pytest

from core import ai, config, intel

VULNERABLE = {
    "scan_id": 7, "target": "lab.ornek.com", "resolved_ip": "203.0.113.5", "scan_time": "2026-10-02 10:00:00",
    "scanned_ports": 1000, "duration": 2.1, "total_open": 5, "overall_risk": 100,
    "risk_level": {"key": "critical", "label": "Kritik Risk"},
    "analysis": [
        {"port": 21, "protocol": "TCP", "service": "FTP", "banner": "220 (vsFTPd 2.3.4)", "risk": 100},
        {"port": 22, "protocol": "TCP", "service": "SSH", "banner": "SSH-2.0-OpenSSH_5.3", "risk": 80},
        {"port": 80, "protocol": "TCP", "service": "HTTP", "banner": "Apache/2.4.49 (Unix)", "risk": 100},
        {"port": 3306, "protocol": "TCP", "service": "MySQL", "banner": "", "risk": 50},
        {"port": 3389, "protocol": "TCP", "service": "RDP", "banner": "", "risk": 40},
    ],
    "cve_alerts": ["[Port 21] vsFTPd 2.3.4 arka kapı zafiyeti (CVE-2011-2523).",
                   "[Port 80] Apache 2.4.49/2.4.50 Path Traversal & RCE (CVE-2021-41773 / CVE-2021-42013)."],
    "findings": [
        {"plugin": "http_headers", "port": 80, "severity": "medium", "title": "Eksik başlık: content-security-policy", "detail": ""},
        {"plugin": "http_headers", "port": 80, "severity": "low", "title": "Sürüm ifşası: server: Apache/2.4.49", "detail": ""},
    ],
    "recommendations": [],
}
CLEAN = {**VULNERABLE, "total_open": 1, "overall_risk": 1, "risk_level": {"key": "low", "label": "Düşük Risk"},
         "analysis": [{"port": 443, "protocol": "TCP", "service": "HTTPS", "banner": "", "risk": 4}],
         "cve_alerts": [], "findings": []}


def techniques(result):
    return {t["id"]: t for tac in result["tactics"] for t in tac["techniques"]}


def test_attack_mapping_builds_kill_chain():
    result = intel.attack_mapping(VULNERABLE)
    techs = techniques(result)
    assert {"T1595", "T1190", "T1133", "T1110", "T1021.001", "T1021.004", "T1485", "T1486", "T1505.003"} <= set(techs)
    assert techs["T1190"]["ports"] == [21, 80]
    assert techs["T1021.004"]["url"] == "https://attack.mitre.org/techniques/T1021/004/"
    tactics = [c["tactic_id"] for c in result["chain"]]
    assert tactics[0] == "TA0043" and tactics[-1] == "TA0040"
    assert tactics == sorted(tactics, key=intel.TACTIC_INDEX.get)  # matris sırasında
    assert result["narrative"].startswith("Olası saldırı yolu:")
    assert intel.attack_mapping({**CLEAN, "analysis": []})["chain"] == []


def test_scorecard_grades_and_caps():
    bad = intel.scorecard(VULNERABLE)
    assert bad["grade"] in ("D", "F") and bad["caps"]
    cats = {c["key"]: c for c in bad["categories"]}
    assert cats["patching"]["score"] == 10 and cats["encryption"]["score"] == 60  # FTP -20, yalnızca HTTP -20
    good = intel.scorecard(CLEAN)
    assert good["grade"] == "A+" and good["score"] == 100 and not good["caps"]
    # Veritabanı dışarıdaysa CVE olmasa da not en fazla C
    db_only = {**CLEAN, "analysis": CLEAN["analysis"] + [{"port": 5432, "service": "PostgreSQL", "banner": ""}]}
    assert intel.scorecard(db_only)["grade"] in ("C", "D", "F")
    assert [intel.grade_of(s) for s in (100, 90, 75, 60, 45, 10)] == ["A+", "A", "B", "C", "D", "F"]


def test_compliance_statuses():
    comp = intel.compliance(VULNERABLE)
    status = {c["id"]: c["status"] for c in comp["controls"]}
    assert status["A.8.8"] == "fail" and status["A.8.22"] == "fail" and status["KVKK m.12"] == "fail"
    assert status["A.8.16"] == "partial"
    assert intel.compliance(CLEAN, monitored=True)["controls"][-2]["status"] == "pass"
    clean = intel.compliance(CLEAN, monitored=True)
    assert clean["summary"]["fail"] == 0 and clean["score"] >= 90
    assert "resmi denetim" in clean["disclaimer"]


def test_offline_analyst_summary_and_port_question(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    data = intel.analyze(VULNERABLE)
    result = asyncio.run(ai.analyze(VULNERABLE, data))
    assert result["engine"] == "kural"
    text = result["answer"]
    for heading in ("## Yönetici özeti", "## Saldırgan gözünden", "## Öncelikli aksiyon planı", "## Uyum notu"):
        assert heading in text
    assert "**[P1 · 24 saat]**" in text and "72 saat" in text
    answer = asyncio.run(ai.analyze(VULNERABLE, data, "3306 neden riskli?"))["answer"]
    assert answer.startswith("## 3306/MySQL") and "T1485" in answer
    other = asyncio.run(ai.analyze(VULNERABLE, data, "Genel durum nedir?"))["answer"]
    assert "ANTHROPIC_API_KEY" in other


def test_claude_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")

    async def broken(*args, **kwargs):
        raise ConnectionError("ağ yok")

    monkeypatch.setattr(ai, "ask_claude", broken)
    result = asyncio.run(ai.analyze(VULNERABLE, intel.analyze(VULNERABLE)))
    assert result["engine"] == "kural" and "Claude'a ulaşılamadı" in result["answer"]


def test_context_marks_banners_as_data():
    ctx = ai.build_context(VULNERABLE, intel.analyze(VULNERABLE))
    assert "vsFTPd 2.3.4" in ctx and "CVE-2011-2523" in ctx
    assert "<rapor_verisi>" in ai.SYSTEM_PROMPT and "güvenilmez" in ai.SYSTEM_PROMPT


# ---------------------------------------------------------------- API
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "intel.db"))
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    import main

    with TestClient(main.app) as c:
        c.post("/auth/register", json={"email": "intel@example.com", "password": "parola123"})
        yield c


def scan(client):
    return client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3, "timeout": 0.2}).json()


def test_intel_endpoint_available_on_free(client):
    sid = scan(client)["scan_id"]
    data = client.get(f"/api/scans/{sid}/intel").json()
    assert set(data) == {"scorecard", "attack", "compliance"}
    assert client.get("/api/scans/9999/intel").status_code == 404


def test_ai_requires_pro_max_caches_summary_and_counts_quota(client):
    sid = scan(client)["scan_id"]
    assert client.post(f"/api/scans/{sid}/ai", json={}).status_code == 402
    client.post("/api/billing/checkout", json={"plan": "pro_max"})
    first = client.post(f"/api/scans/{sid}/ai", json={}).json()
    assert first["engine"] == "kural" and "## Yönetici özeti" in first["answer"]
    again = client.post(f"/api/scans/{sid}/ai", json={}).json()
    assert again["id"] == first["id"]  # önbellekten, kota harcamaz
    client.post(f"/api/scans/{sid}/ai", json={"question": "Ne yapmalıyım?"})
    info = client.get(f"/api/scans/{sid}/ai").json()
    assert info["used"] == 2 and len(info["notes"]) == 2 and info["daily"] == 20
    assert client.get("/api/me").json()["subscription"]["usage"]["ai_today"] == 2


def test_share_link_lifecycle(client):
    sid = scan(client)["scan_id"]
    assert client.post(f"/api/scans/{sid}/share").status_code == 402
    client.post("/api/billing/checkout", json={"plan": "pro"})
    url = client.post(f"/api/scans/{sid}/share").json()["url"]
    token = url.rsplit("/", 1)[-1]
    assert client.post(f"/api/scans/{sid}/share").json()["url"] == url  # aynı bağlantı
    client.cookies.clear()
    page = client.get(f"/share/{token}")
    assert page.status_code == 200 and "salt-okunur" in page.text and "Güvenlik Karnesi" in page.text
    assert page.headers["x-robots-tag"] == "noindex, nofollow"
    assert client.get("/share/yanlis-anahtar-yanlis-anahtar").status_code == 404
    client.post("/auth/login", json={"email": "intel@example.com", "password": "parola123"})
    client.delete(f"/api/scans/{sid}/share")
    client.cookies.clear()
    assert client.get(f"/share/{token}").status_code == 404


def test_printable_report_includes_intel(client):
    client.post("/api/billing/checkout", json={"plan": "pro"})
    sid = scan(client)["scan_id"]
    page = client.get(f"/reports/{sid}")
    assert "MITRE ATT&amp;CK" in page.text and "KVKK" in page.text


def test_kill_chain_uses_each_technique_once_and_turkish_case():
    chain = intel.attack_mapping(VULNERABLE)["chain"]
    ids = [c["technique"] for c in chain]
    assert len(ids) == len(set(ids))
    assert dict((c["tactic_id"], c["technique"]) for c in chain)["TA0001"] == "T1190"  # CVE istismarı öne çıkar
    narrative = intel.attack_mapping(VULNERABLE)["narrative"]
    assert "ilk erişim" in narrative and "i̇" not in narrative
    assert intel.tr_lower("İLK ERİŞİM · DIŞ") == "ilk erişim · dış"
