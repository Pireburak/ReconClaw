import sqlite3

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import auth, config, plans  # noqa: E402

ADMIN = "yonetici@example.com"


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "admin.db"))
    monkeypatch.setattr(config, "ADMIN_EMAILS", {ADMIN})
    import main

    with TestClient(main.app) as c:
        yield c


def register(client, email, password="parola123"):
    client.cookies.clear()
    res = client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    if email == ADMIN:
        auth.sync_admins()  # açılışta yapılan senkronizasyon (parolalı kayıt anında yönetici olmaz)
        return client.get("/api/me").json()
    return res.json()["user"]


def test_admin_email_gets_unlimited_admin_plan(app_client):
    user = register(app_client, ADMIN)
    assert user["role"] == "admin" and user["is_admin"] is True
    sub = app_client.get("/api/me").json()["subscription"]
    assert sub["admin"] is True and sub["plan"]["id"] == "admin" and sub["plan"]["daily_scans"] == plans.UNLIMITED
    # Sınırsız: geniş port aralığı, kotasız tarama, API anahtarı
    res = app_client.post("/api/scan", json={"target": "127.0.0.1", "max_port": 30000, "timeout": 0.2})
    assert res.status_code == 200
    assert app_client.post("/api/me/token").status_code == 200
    # Yönetici için demo ödeme kapalı
    assert app_client.post("/api/billing/checkout", json={"plan": "pro"}).status_code == 400


def test_password_signup_with_admin_email_is_not_instant_admin(app_client):
    # E-posta doğrulanmadığı için adresi önce alan kişi yönetici olamaz
    res = app_client.post("/auth/register", json={"email": ADMIN, "password": "parola123"})
    assert res.json()["user"]["role"] == "user"
    # Sağlayıcının doğruladığı e-postayla sosyal giriş ise anında yönetici olur
    uid = auth.login_with_identity("github", "42", "oauth-yonetici@example.com", "Sahip", True)
    assert auth.get_user(uid)["role"] == "user"  # listede değil
    import core.config as cfg
    cfg.ADMIN_EMAILS.add("oauth-sahip@example.com")
    uid = auth.login_with_identity("github", "43", "oauth-sahip@example.com", "Sahip", True)
    assert auth.get_user(uid)["role"] == "admin"


def test_regular_user_cannot_open_admin_panel(app_client):
    register(app_client, "uye@example.com")
    assert app_client.get("/api/me").json()["role"] == "user"
    # Panel yönetici olmayanlara hiç yokmuş gibi görünür: 404, API belgesinde ve sayfa kodunda iz yok
    for path in ("/api/admin/overview", "/api/admin/users", "/api/admin/audit"):
        assert app_client.get(path).status_code == 404
    assert app_client.patch("/api/admin/users/1", json={"role": "admin"}).status_code == 404
    assert "/api/admin" not in app_client.get("/openapi.json").text
    assert "admin" not in app_client.get("/api/plans").json()
    page = app_client.get("/").text
    assert "admin.js" not in page and "YÖNETİM" not in page
    assert "YÖNETİM" not in app_client.get("/static/js/app.js").text
    app_client.cookies.clear()
    assert app_client.get("/api/admin/overview").status_code == 404


def test_admin_manages_users_and_audit(app_client):
    member = register(app_client, "uye@example.com")
    app_client.post("/auth/login", json={"email": "uye@example.com", "password": "yanlis-parola1"})
    register(app_client, ADMIN)

    overview = app_client.get("/api/admin/overview").json()
    assert overview["users_total"] == 2 and overview["admins"] == 1
    assert overview["failed_logins_24h"] == 1
    assert {p["id"] for p in overview["by_plan"]} == set(plans.PLANS)

    users = app_client.get("/api/admin/users?q=uye").json()
    assert [u["email"] for u in users] == ["uye@example.com"]

    # Süresiz Ultra Max ataması (ödeme kaydı oluşmaz) ve MRR'a yansıması
    updated = app_client.patch(f"/api/admin/users/{member['id']}", json={"plan": "ultra_max"}).json()
    assert updated["plan"] == "ultra_max" and updated["plan_expires"] is None and updated["paid"] == 0
    assert app_client.get("/api/admin/overview").json()["mrr"] == 1999

    # Askıya alınan kullanıcı giriş yapamaz
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"disabled": True}).json()["disabled"] is True
    me = app_client.get("/api/me").json()
    app_client.cookies.clear()
    res = app_client.post("/auth/login", json={"email": "uye@example.com", "password": "parola123"})
    assert res.status_code == 400 and "askıya" in res.json()["detail"]
    app_client.post("/auth/login", json={"email": ADMIN, "password": "parola123"})

    actions = [e["action"] for e in app_client.get("/api/admin/audit").json()["entries"]]
    assert {"admin_plan", "admin_disable", "login_failed", "register"} <= set(actions)

    # Kendini kilitleme koruması
    assert app_client.patch(f"/api/admin/users/{me['id']}", json={"role": "user"}).status_code == 400
    assert app_client.patch(f"/api/admin/users/{me['id']}", json={"disabled": True}).status_code == 400
    assert app_client.delete(f"/api/admin/users/{me['id']}").status_code == 400

    # Kullanıcıyı yönetici yap, sonra sil
    promoted = app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "admin", "disabled": False}).json()
    assert promoted["role"] == "admin" and promoted["level"] == 6
    # Bir yöneticiyi silmek yalnızca sahibe açık
    assert app_client.delete(f"/api/admin/users/{member['id']}").status_code == 400
    assert auth.set_owner(ADMIN)
    assert app_client.delete(f"/api/admin/users/{member['id']}").status_code == 200
    assert app_client.get("/api/admin/overview").json()["users_total"] == 1


def test_sync_admins_promotes_existing_account(app_client, monkeypatch):
    register(app_client, "sonradan@example.com")
    monkeypatch.setattr(config, "ADMIN_EMAILS", {"sonradan@example.com"})
    assert auth.sync_admins() == 1
    assert app_client.get("/api/me").json()["is_admin"] is True


def test_user_sees_own_security_log(app_client):
    register(app_client, "log@example.com")
    app_client.post("/auth/logout")
    app_client.post("/auth/login", json={"email": "log@example.com", "password": "hatali-parola9"})
    app_client.post("/auth/login", json={"email": "log@example.com", "password": "parola123"})
    entries = app_client.get("/api/me/audit").json()
    assert [e["action"] for e in entries][:3] == ["login", "login_failed", "register"]
    assert entries[1]["label"] == "Hatalı giriş denemesi"


def test_manage_cli_promotes_user(app_client, tmp_path):
    register(app_client, "cli@example.com")
    import manage

    assert manage.main(["make-admin", "cli@example.com"]) == 0
    assert manage.main(["make-admin", "yok@example.com"]) == 1
    from core import db_manager

    conn = sqlite3.connect(db_manager.DB_PATH)
    assert conn.execute("SELECT role FROM users WHERE email = 'cli@example.com'").fetchone()[0] == "admin"
    conn.close()


def test_owner_rules(app_client, tmp_path):
    owner = register(app_client, "sahip@example.com")
    other = register(app_client, "ikinci@example.com")
    member = register(app_client, "uye2@example.com")
    import manage

    assert manage.main(["make-owner", "sahip@example.com"]) == 0
    assert manage.main(["make-admin", "ikinci@example.com"]) == 0
    # ikinci yönetici olarak giriş
    app_client.cookies.clear()
    app_client.post("/auth/login", json={"email": "ikinci@example.com", "password": "parola123"})
    assert app_client.get("/api/me").json()["is_admin"] is True
    # Yönetici üyeyi yönetici yapabilir, ama sahibe ve diğer yöneticiye dokunamaz
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "admin"}).status_code == 200
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "user"}).status_code == 400
    for body in ({"role": "user"}, {"disabled": True}, {"plan": "pro"}):
        assert app_client.patch(f"/api/admin/users/{owner['id']}", json=body).status_code == 400
    assert app_client.delete(f"/api/admin/users/{owner['id']}").status_code == 400
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "owner"}).status_code == 422
    # Sahip yöneticinin yetkisini alabilir
    app_client.cookies.clear()
    app_client.post("/auth/login", json={"email": "sahip@example.com", "password": "parola123"})
    me = app_client.get("/api/me").json()
    assert me["is_owner"] and me["subscription"]["admin"]
    assert app_client.patch(f"/api/admin/users/{other['id']}", json={"role": "user"}).json()["role"] == "user"
    roles = {u["email"]: u["role"] for u in app_client.get("/api/admin/users").json()}
    assert roles["sahip@example.com"] == "owner" and roles["uye2@example.com"] == "admin"
    # Sahiplik devri: önceki sahip yöneticiye iner; tek sahip kalır
    assert manage.main(["make-owner", "uye2@example.com"]) == 0
    roles = {u["email"]: u["role"] for u in app_client.get("/api/admin/users").json()}
    assert roles["sahip@example.com"] == "admin" and roles["uye2@example.com"] == "owner"


def test_sync_admins_never_demotes_owner(app_client, monkeypatch):
    register(app_client, ADMIN)
    assert auth.set_owner(ADMIN)
    auth.sync_admins()
    assert app_client.get("/api/me").json()["role"] == "owner"


def test_cli_password_reset(app_client, monkeypatch):
    register(app_client, "unuttum@example.com")
    import manage

    monkeypatch.setattr("getpass.getpass", lambda prompt="": "YeniParola42")
    assert manage.main(["passwd", "unuttum@example.com"]) == 0
    app_client.cookies.clear()
    assert app_client.get("/api/me").status_code == 401  # eski oturumlar kapandı
    assert app_client.post("/auth/login", json={"email": "unuttum@example.com", "password": "YeniParola42"}).status_code == 200


def test_moderator_sees_panel_but_only_suspends_members(app_client):
    import manage

    member = register(app_client, "uye3@example.com")
    other_mod = register(app_client, "mod2@example.com")
    register(app_client, "mod@example.com")
    assert manage.main(["make-moderator", "mod@example.com"]) == 0
    assert manage.main(["make-moderator", "mod2@example.com"]) == 0
    app_client.cookies.clear()
    app_client.post("/auth/login", json={"email": "mod@example.com", "password": "parola123"})
    me = app_client.get("/api/me").json()
    assert me["role"] == "moderator" and me["is_staff"] and not me["is_admin"]
    assert me["subscription"]["plan"]["id"] == "free"  # moderatör sınırsız plan almaz
    page = app_client.get("/").text
    assert "admin.js" in page and 'data-view="admin"' in page
    overview = app_client.get("/api/admin/overview").json()
    assert overview["mrr"] is None and overview["revenue_total"] is None and overview["can_manage"] is False
    assert all(u["paid"] is None for u in app_client.get("/api/admin/users").json())
    team = {m["email"]: m["role"] for m in app_client.get("/api/admin/team").json()}
    assert team == {"mod@example.com": "moderator", "mod2@example.com": "moderator"}
    # Üyeyi askıya alabilir; rol / plan / silme ve diğer moderatöre dokunma yok
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"disabled": True}).status_code == 200
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"disabled": False}).status_code == 200
    for body in ({"role": "admin"}, {"role": "moderator"}, {"plan": "ultra_max"}):
        assert app_client.patch(f"/api/admin/users/{member['id']}", json=body).status_code == 400
    assert app_client.patch(f"/api/admin/users/{other_mod['id']}", json={"disabled": True}).status_code == 400
    assert app_client.delete(f"/api/admin/users/{member['id']}").status_code == 400


def test_admin_appoints_moderator_and_team_shows_who_granted(app_client):
    member = register(app_client, "aday@example.com")
    register(app_client, ADMIN)
    res = app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "moderator"})
    assert res.status_code == 200 and res.json()["role"] == "moderator"
    team = app_client.get("/api/admin/team").json()
    mod = next(m for m in team if m["email"] == "aday@example.com")
    assert mod["role"] == "moderator" and mod["granted_by"] == ADMIN
    assert [m["role"] for m in team] == ["admin", "moderator"]  # sıralama: sahip, yönetici, moderatör
    # Moderatörün yetkisi geri alınınca panel kendisinden gizlenir
    assert app_client.patch(f"/api/admin/users/{member['id']}", json={"role": "user"}).json()["role"] == "user"
    app_client.cookies.clear()
    app_client.post("/auth/login", json={"email": "aday@example.com", "password": "parola123"})
    assert app_client.get("/api/admin/team").status_code == 404
    assert "admin.js" not in app_client.get("/").text


def test_api_token_cannot_reach_admin(app_client):
    register(app_client, ADMIN)
    token = app_client.post("/api/me/token").json()["token"]
    app_client.cookies.clear()
    assert app_client.get("/api/admin/overview", headers={"Authorization": f"Bearer {token}"}).status_code == 404
