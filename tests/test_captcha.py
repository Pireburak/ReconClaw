import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from core import captcha, config  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "captcha.db"))
    import main

    with TestClient(main.app) as c:
        yield c


def test_honeypot_blocks_bots(client):
    res = client.post("/auth/register", json={"email": "bot@example.com", "password": "parola123", "website": "http://spam"})
    assert res.status_code == 400
    assert client.post("/auth/register", json={"email": "insan@example.com", "password": "parola123", "website": ""}).status_code == 200


def test_turnstile_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(config, "TURNSTILE_SITE_KEY", "0x4AAA-site")
    monkeypatch.setattr(config, "TURNSTILE_SECRET_KEY", "0x4AAA-secret")
    seen = []

    class FakeResponse:
        def __init__(self, ok):
            self.ok = ok

        def json(self):
            return {"success": self.ok}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, data):
            seen.append(data)
            return FakeResponse(data["response"] == "gecerli-jeton")

    monkeypatch.setattr(captcha.httpx, "AsyncClient", FakeClient)
    assert 'data-sitekey="0x4AAA-site"' in client.get("/login").text
    body = {"email": "ts@example.com", "password": "parola123"}
    assert "robot" in client.post("/auth/register", json=body).json()["detail"]
    assert client.post("/auth/register", json={**body, "captcha": "sahte"}).status_code == 400
    assert client.post("/auth/register", json={**body, "captcha": "gecerli-jeton"}).status_code == 200
    assert seen[-1]["secret"] == "0x4AAA-secret"
    client.cookies.clear()
    assert client.post("/auth/login", json=body).status_code == 400
    assert client.post("/auth/login", json={**body, "captcha": "gecerli-jeton"}).status_code == 200


def test_turnstile_off_by_default(client):
    assert captcha.enabled() is False
    assert "cf-turnstile" not in client.get("/login").text
