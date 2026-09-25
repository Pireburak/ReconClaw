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
