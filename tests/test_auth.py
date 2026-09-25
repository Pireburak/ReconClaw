import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import auth, config, oauth  # noqa: E402


@pytest.fixture
def db(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "auth.db"))
    db_manager.init_db()


@pytest.fixture
def client(db):
    import main

    with TestClient(main.app) as c:
        yield c


def test_password_hashing():
    stored = auth.hash_password("gizli-parola1")
    assert stored.startswith("scrypt$") and "gizli" not in stored
    assert auth.verify_password("gizli-parola1", stored)
    assert not auth.verify_password("yanlis-parola1", stored)
    assert not auth.verify_password("x", None)
    assert not auth.verify_password("x", "bozuk$format")


def test_register_login_logout(client):
    res = client.post("/auth/register", json={"email": "Ali@Example.com", "password": "parola123", "name": "Ali"})
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "ali@example.com"
    assert auth.SESSION_COOKIE in res.cookies
    assert client.get("/api/me").json()["name"] == "Ali"

    client.post("/auth/logout")
    assert client.get("/api/me").status_code == 401

    assert client.post("/auth/login", json={"email": "ali@example.com", "password": "yanlis123"}).status_code == 400
    assert client.post("/auth/login", json={"email": "ALI@example.com", "password": "parola123"}).status_code == 200
    assert client.get("/api/me").status_code == 200


def test_register_validation(client, monkeypatch):
    bad = [
        {"email": "gecersiz", "password": "parola123"},
        {"email": "a@b.co", "password": "kisa1"},
        {"email": "a@b.co", "password": "sadeceharf"},
    ]
    for body in bad:
        assert client.post("/auth/register", json=body).status_code == 400
    assert client.post("/auth/register", json={"email": "a@b.co", "password": "parola123"}).status_code == 200
    assert client.post("/auth/register", json={"email": "A@B.co", "password": "parola123"}).status_code == 400

    monkeypatch.setattr(config, "ALLOW_SIGNUP", False)
    res = client.post("/auth/register", json={"email": "yeni@b.co", "password": "parola123"})
    assert res.status_code == 400 and "kapatıldı" in res.json()["detail"]


def test_change_password_revokes_other_sessions(client):
    client.post("/auth/register", json={"email": "p@x.io", "password": "parola123"})
    import main

    with TestClient(main.app) as other:
        other.post("/auth/login", json={"email": "p@x.io", "password": "parola123"})
        assert other.get("/api/me").status_code == 200
        assert client.post("/api/me/password", json={"current": "yanlis", "new": "yeniparola1"}).status_code == 400
        assert client.post("/api/me/password", json={"current": "parola123", "new": "yeniparola1"}).status_code == 200
        assert other.get("/api/me").status_code == 401
    assert client.get("/api/me").status_code == 200


def test_delete_account(client):
    client.post("/auth/register", json={"email": "sil@x.io", "password": "parola123"})
    assert client.request("DELETE", "/api/me", json={"confirm_email": "baska@x.io"}).status_code == 400
    assert client.request("DELETE", "/api/me", json={"confirm_email": "sil@x.io"}).status_code == 200
    assert client.post("/auth/login", json={"email": "sil@x.io", "password": "parola123"}).status_code == 400


def test_social_login_links_only_verified_email(db):
    user_id = auth.create_user("veli@example.com", "Veli", "parola123")

    # Doğrulanmamış e-posta mevcut hesaba bağlanmaz (hesap ele geçirme koruması)
    with pytest.raises(auth.AuthError):
        auth.login_with_identity("microsoft", "ms-1", "veli@example.com", "Sahte", email_verified=False)

    assert auth.login_with_identity("github", "gh-1", "veli@example.com", "Veli", email_verified=True) == user_id
    # Aynı kimlikle ikinci giriş aynı kullanıcıya gider
    assert auth.login_with_identity("github", "gh-1", "degisti@example.com", "Veli", email_verified=False) == user_id

    new_id = auth.login_with_identity("google", "g-9", "yeni@example.com", "Yeni", email_verified=True)
    assert new_id != user_id
    assert auth.public_user(auth.get_user(new_id))["has_password"] is False


def test_first_user_claims_legacy_scans(db):
    from core import db_manager

    report = {"target": "eski.com", "resolved_ip": "1.2.3.4", "total_open": 0, "overall_risk": 0,
              "risk_level": {"key": "low", "label": "Düşük Risk"}, "duration": 1, "scan_time": "2026-01-01 10:00:00",
              "analysis": [], "findings": []}
    db_manager.save_scan(report)
    user_id = auth.create_user("ilk@example.com", "İlk", "parola123")
    assert [r["target"] for r in db_manager.get_recent_scans(user_id=user_id)] == ["eski.com"]


def test_oauth_provider_config_and_redirect(client, monkeypatch):
    assert all(not p["enabled"] for p in client.get("/auth/providers").json())
    res = client.get("/auth/google/login", follow_redirects=False)
    assert "/login?error=" in res.headers["location"]

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "sec")
    res = client.get("/auth/google/login", follow_redirects=False)
    location = res.headers["location"]
    assert location.startswith("https://accounts.google.com/")
    assert "code_challenge_method=S256" in location and "state=" in location
    assert "redirect_uri=http%3A%2F%2Ftestserver%2Fauth%2Fgoogle%2Fcallback" in location


def test_oauth_callback_rejects_bad_state(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "sec")
    res = client.get("/auth/github/callback?code=abc&state=sahte", follow_redirects=False)
    assert res.headers["location"].startswith("/login?error=")


def test_oauth_callback_full_flow(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "sec")

    async def fake_complete(provider, code, redirect, verifier, form):
        assert code == "kod123"
        return {"subject": "42", "email": "octo@example.com", "email_verified": True, "name": "Octo", "avatar_url": None}

    monkeypatch.setattr(oauth, "complete_login", fake_complete)
    state, _ = oauth.new_state("github")
    res = client.get(f"/auth/github/callback?code=kod123&state={state}", follow_redirects=False)
    assert res.headers["location"] == "/"
    assert client.get("/api/me").json()["providers"] == ["github"]
    # state tek kullanımlıktır
    res = client.get(f"/auth/github/callback?code=kod123&state={state}", follow_redirects=False)
    assert res.headers["location"].startswith("/login?error=")
