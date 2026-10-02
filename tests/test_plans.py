import sqlite3
from datetime import datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import config, plans, verify  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "plans.db"))
    import main

    with TestClient(main.app) as c:
        c.post("/auth/register", json={"email": "plan@example.com", "password": "parola123"})
        yield c


def scan(client, **extra):
    return client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3, "timeout": 0.2, **extra})


def test_plan_catalog():
    ids = list(plans.PLANS)
    assert ids == ["free", "pro", "pro_max", "ultra", "ultra_max"]
    levels = [p.level for p in plans.PLANS.values()]
    assert levels == sorted(levels) == [1, 2, 3, 4, 5]
    assert plans.PLANS["pro"].price_yearly == plans.PLANS["pro"].price_monthly * 10
    # Ultra Max ₺5.500 ve sınırlıdır; sınırsız erişim yalnızca yöneticilere (Admin seviyesi) verilir
    assert plans.PLANS["ultra_max"].price_monthly == 5500
    assert all(p.daily_scans != plans.UNLIMITED for p in plans.PLANS.values())
    assert plans.ADMIN_PLAN.daily_scans == plans.UNLIMITED and "admin" not in plans.PLANS


def test_new_user_is_free_and_sees_usage(client):
    sub = client.get("/api/me").json()["subscription"]
    assert sub["plan"]["id"] == "free" and sub["usage"]["scans_today"] == 0
    assert scan(client).status_code == 200
    assert client.get("/api/billing").json()["usage"]["scans_today"] == 1


def test_free_limits_return_402(client):
    res = scan(client, max_port=500)
    assert res.status_code == 402 and res.json()["upgrade"] is True
    report = scan(client).json()
    assert client.get(f"/api/scans/{report['scan_id']}/csv").status_code == 402
    assert client.get(f"/api/compare?old={report['scan_id']}&new={report['scan_id']}").status_code == 402
    assert client.post("/api/me/token").status_code == 402
    page = client.get(f"/reports/{report['scan_id']}", follow_redirects=False)
    assert page.headers["location"] == "/#plans"


def test_free_plan_skips_plugins(client, monkeypatch):
    called = []

    async def fake_plugins(*args, **kwargs):
        called.append(True)
        return []

    import main

    monkeypatch.setattr(main, "run_plugins", fake_plugins)
    monkeypatch.setattr(main.AsyncScanner, "run", fake_run)
    scan(client, plugins=True)
    assert called == []
    client.post("/api/billing/checkout", json={"plan": "pro"})
    scan(client, plugins=True)
    assert called == [True]


async def fake_run(self):
    from core.engine import ScanResult
    return ScanResult(self.target, self.ip, [{"port": 80, "protocol": "TCP", "banner": ""}], 0.01)


def test_daily_quota_survives_deleting_scans(client):
    user_id = client.get("/api/me").json()["id"]
    for _ in range(plans.PLANS["free"].daily_scans):
        plans.record_scan(user_id)
    client.delete("/api/scans")
    res = scan(client)
    assert res.status_code == 402 and "günlük" in res.json()["detail"]


def test_per_minute_limit_follows_plan(client):
    assert scan(client).status_code == 200
    assert scan(client).status_code == 200
    assert scan(client).status_code == 429  # Free: dakikada 2


def test_checkout_upgrade_yearly_and_cancel(client):
    res = client.post("/api/billing/checkout", json={"plan": "ultra", "period": "yearly"}).json()
    assert res["plan"]["id"] == "ultra" and res["mode"] == "demo"
    assert res["amount"] == plans.PLANS["ultra"].price_yearly
    expires = datetime.fromisoformat(res["expires"])
    assert timedelta(days=364) < expires - datetime.now() < timedelta(days=366)
    assert scan(client, max_port=20000).status_code == 200

    pays = client.get("/api/billing").json()["payments"]
    assert pays[0]["status"] == "demo" and pays[0]["plan"] == "ultra"

    assert client.post("/api/billing/cancel").json()["plan"]["id"] == "free"
    assert client.post("/api/billing/checkout", json={"plan": "bilinmeyen"}).status_code == 422
    assert client.post("/api/billing/checkout", json={"plan": "pro", "period": "haftalik"}).status_code == 422


def test_expired_plan_falls_back_to_free(client):
    from core import db_manager

    client.post("/api/billing/checkout", json={"plan": "pro"})
    conn = sqlite3.connect(db_manager.DB_PATH)
    conn.execute("UPDATE users SET plan_expires = '2000-01-01 00:00:00'")
    conn.commit()
    conn.close()
    sub = client.get("/api/me").json()["subscription"]
    assert sub["plan"]["id"] == "free" and sub["expired"] is True


def test_api_token_stops_working_after_downgrade(client):
    client.post("/api/billing/checkout", json={"plan": "pro_max"})
    token = client.post("/api/me/token").json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/me", headers=headers).status_code == 200
    client.post("/api/billing/cancel")
    assert client.get("/api/me", headers=headers).status_code == 402


def test_plans_endpoint_is_public(client):
    client.post("/auth/logout")
    data = client.get("/api/plans").json()
    assert [p["name"] for p in data["plans"]] == ["Free", "Pro", "Pro Max", "Ultra", "Ultra Max"]
    assert data["payment_mode"] == "demo"


def test_target_limits_and_verification(client, monkeypatch):
    first = client.post("/api/targets", json={"host": "https://Ornek.com/yol"}).json()
    assert first["host"] == "ornek.com" and first["token"].startswith("reconclaw-verify=")
    assert client.post("/api/targets", json={"host": "ornek.com"}).status_code == 400
    assert client.post("/api/targets", json={"host": "ikinci.com"}).status_code == 402  # Free: 1 hedef
    assert client.post("/api/targets", json={"host": "geçersiz hedef"}).status_code == 422

    async def found(client_, host, token):
        return True

    async def missing(client_, host, token):
        return False

    monkeypatch.setattr(verify, "_check_dns", missing)
    monkeypatch.setattr(verify, "_check_file", missing)
    assert client.post(f"/api/targets/{first['id']}/verify").status_code == 400
    monkeypatch.setattr(verify, "_check_file", found)
    assert client.post(f"/api/targets/{first['id']}/verify").json()["method"] == "file"
    assert client.get("/api/targets").json()["targets"][0]["verified_at"]
    assert client.delete(f"/api/targets/{first['id']}").status_code == 200


def test_required_verification_blocks_unverified_targets(client, monkeypatch):
    monkeypatch.setattr(config, "REQUIRE_TARGET_VERIFICATION", True)
    res = scan(client)
    assert res.status_code == 403 and "doğrulanmış" in res.json()["detail"]

    target = client.post("/api/targets", json={"host": "127.0.0.1"}).json()

    async def found(client_, host, token):
        return True

    monkeypatch.setattr(verify, "_check_file", found)
    client.post(f"/api/targets/{target['id']}/verify")
    assert scan(client).status_code == 200
    verify.ensure_allowed(1, "scanme.nmap.org")  # her zaman izinli test sunucusu
