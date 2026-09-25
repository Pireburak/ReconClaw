import sqlite3

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "test.db"))
    import main

    with TestClient(main.app) as c:
        res = c.post("/auth/register", json={"email": "test@example.com", "password": "parola123", "name": "Test"})
        assert res.status_code == 200
        yield c


def test_scan_is_saved_and_can_be_reopened(client):
    res = client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 5, "timeout": 0.3})
    assert res.status_code == 200
    report = res.json()
    assert report["resolved_ip"] == "127.0.0.1"
    assert report["scanned_ports"] == 5
    assert "findings" in report

    history = client.get("/api/history").json()
    assert history[0]["id"] == report["scan_id"]
    assert history[0]["has_report"] == 1

    detail = client.get(f"/api/scans/{report['scan_id']}").json()
    assert detail == report


def test_errors(client):
    assert client.post("/api/scan", json={"target": "geçersiz hedef"}).status_code == 422
    assert client.post("/api/scan", json={"target": "x.com", "max_port": 70000}).status_code == 422
    assert client.post("/api/scan", json={"target": "yok.invalid"}).status_code == 400
    assert client.get("/api/scans/9999").status_code == 404


def test_api_requires_login(client):
    client.post("/auth/logout")
    assert client.post("/api/scan", json={"target": "127.0.0.1"}).status_code == 401
    assert client.get("/api/history").status_code == 401
    assert client.get("/", follow_redirects=False).headers["location"] == "/login"


def test_scans_are_private_per_user(client):
    report = client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3, "timeout": 0.3}).json()
    client.post("/auth/logout")
    client.post("/auth/register", json={"email": "other@example.com", "password": "baska-parola9"})
    assert client.get("/api/history").json() == []
    assert client.get(f"/api/scans/{report['scan_id']}").status_code == 404
    assert client.delete(f"/api/scans/{report['scan_id']}").status_code == 404


def test_csv_report_compare_stats_and_delete(client):
    first = client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3, "timeout": 0.3}).json()
    second = client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3, "timeout": 0.3}).json()

    csv_res = client.get(f"/api/scans/{first['scan_id']}/csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")

    page = client.get(f"/reports/{first['scan_id']}")
    assert page.status_code == 200 and "127.0.0.1" in page.text

    diff = client.get(f"/api/compare?old={first['scan_id']}&new={second['scan_id']}").json()
    assert diff["same_target"] is True and diff["risk_delta"] == 0

    stats = client.get("/api/stats").json()
    assert stats["total_scans"] == 2 and stats["domains_scanned"] == 1
    assert stats["db_status"] == "ONLINE"

    assert client.delete(f"/api/scans/{first['scan_id']}").json() == {"deleted": 1}
    assert client.delete("/api/scans").json() == {"deleted": 1}
    assert client.get("/api/history").json() == []


def test_private_targets_can_be_blocked(client, monkeypatch):
    from core import config

    monkeypatch.setattr(config, "ALLOW_PRIVATE_TARGETS", False)
    res = client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 3})
    assert res.status_code == 403


def test_api_token(client):
    token = client.post("/api/me/token").json()["token"]
    client.post("/auth/logout")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/me", headers=headers).json()["email"] == "test@example.com"
    assert client.get("/api/me", headers={"Authorization": "Bearer rc_yanlis"}).status_code == 401


def test_security_headers(client):
    res = client.get("/login")
    assert res.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in res.headers["content-security-policy"]


def test_plugins_endpoint(client):
    names = {p["name"]: p for p in client.get("/api/plugins").json()}
    assert names["http_headers"]["enabled"] is True
    assert 443 in names["tls_cert"]["ports"]


def test_old_database_is_migrated(tmp_path, monkeypatch):
    from core import db_manager

    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE scans (id INTEGER PRIMARY KEY, target_ip TEXT NOT NULL, status TEXT NOT NULL)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(db_manager, "DB_PATH", str(path))
    db_manager.init_db()
    tables = {r[0] for r in sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"scans", "scans_legacy", "open_ports", "findings"} <= tables
