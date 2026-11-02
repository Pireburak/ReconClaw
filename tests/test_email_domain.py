import asyncio
import sqlite3

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import auth, config, verify  # noqa: E402


@pytest.fixture
def app(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "email_domain.db"))
    monkeypatch.setattr(config, "REQUIRE_TARGET_VERIFICATION", True)
    monkeypatch.setattr(config, "REQUIRE_EMAIL_VERIFICATION", False)
    import main

    with TestClient(main.app) as c:
        yield c


def register(client, email):
    client.cookies.clear()
    res = client.post("/auth/register", json={"email": email, "password": "parola123"})
    assert res.status_code == 200, res.text
    return res.json()["user"]


def mark_verified(user_id, by="oauth"):
    from core import db_manager

    conn = sqlite3.connect(db_manager.DB_PATH)
    conn.execute("UPDATE users SET email_verified = 1, email_verified_by = ? WHERE id = ?", (by, user_id))
    conn.commit()
    conn.close()


def test_verified_corporate_email_claims_own_domain_and_subdomains(app):
    user = register(app, "ali@firma-ornek.com")
    status = app.get("/api/targets").json()["email_domain"]
    assert status["domain"] == "firma-ornek.com" and status["eligible"] and not status["verified"]
    # Doğrulanmamış e-postayla alan adı açılamaz
    assert app.post("/api/targets/email-domain", json={"confirm": True}).status_code == 400

    mark_verified(user["id"])
    # Yetkili olduğunu onaylamadan eklenemez
    assert app.post("/api/targets/email-domain", json={"confirm": False}).status_code == 400
    res = app.post("/api/targets/email-domain", json={"confirm": True})
    assert res.status_code == 200 and res.json()["host"] == "firma-ornek.com"
    assert app.get("/api/targets").json()["email_domain"]["claimed"] is True

    verify.ensure_allowed(user["id"], "firma-ornek.com")
    verify.ensure_allowed(user["id"], "www.firma-ornek.com")
    verify.ensure_allowed(user["id"], "https://mail.firma-ornek.com/giris")
    # Benzer ama farklı alan adları ve başka şirketler yasak
    for other in ("kotufirma-ornek.com", "firma-ornek.com.evil.net", "baskafirma.com"):
        with pytest.raises(verify.VerifyError):
            verify.ensure_allowed(user["id"], other)

    actions = [e["action"] for e in app.get("/api/me/audit").json()]
    assert "target_email_claim" in actions


def test_personal_and_public_sector_emails_cannot_claim(app):
    for email in ("biri@gmail.com", "biri@outlook.com", "ogrenci@ogr.istinye.edu.tr",
                  "memur@icisleri.gov.tr", "asker@tsk.mil.tr"):
        user = register(app, email)
        mark_verified(user["id"])
        status = app.get("/api/targets").json()["email_domain"]
        assert status["eligible"] is False, email
        assert app.post("/api/targets/email-domain", json={"confirm": True}).status_code == 400, email
        with pytest.raises(verify.VerifyError):
            verify.ensure_allowed(user["id"], email.split("@")[1])


def test_other_users_domain_claim_does_not_leak(app):
    owner = register(app, "sahibi@firma-ornek.com")
    mark_verified(owner["id"])
    assert app.post("/api/targets/email-domain", json={"confirm": True}).status_code == 200
    stranger = register(app, "yabanci@baska-ornek.com")
    with pytest.raises(verify.VerifyError):
        verify.ensure_allowed(stranger["id"], "firma-ornek.com")


def test_dns_verified_apex_covers_subdomains_but_file_does_not(app, monkeypatch):
    from core import plans

    user = register(app, "dns@kisisel-ornek.com")
    plans.grant(user["id"], "pro")  # 3 hedef hakkı (Free planda 1)
    apex = app.post("/api/targets", json={"host": "firma-ornek.com"}).json()

    async def found_dns(client_, host, token):
        return True

    monkeypatch.setattr(verify, "_is_public_host", lambda host: True)
    monkeypatch.setattr(verify, "_check_dns", found_dns)
    assert app.post(f"/api/targets/{apex['id']}/verify").json()["method"] == "dns"
    verify.ensure_allowed(user["id"], "www.firma-ornek.com")

    # Dosya yöntemi yalnızca o sunucuyu kanıtlar, alt alan adlarını kapsamaz
    other = app.post("/api/targets", json={"host": "site-ornek.com"}).json()
    assert other["id"]

    async def no_dns(client_, host, token):
        return False

    async def found_file(client_, host, token):
        return True

    monkeypatch.setattr(verify, "_check_dns", no_dns)
    monkeypatch.setattr(verify, "_check_file", found_file)
    assert app.post(f"/api/targets/{other['id']}/verify").json()["method"] == "file"
    verify.ensure_allowed(user["id"], "site-ornek.com")
    with pytest.raises(verify.VerifyError):
        verify.ensure_allowed(user["id"], "www.site-ornek.com")


def test_dns_txt_on_parent_domain_verifies_subdomain(monkeypatch):
    asked = []

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    class FakeClient:
        async def get(self, url, params=None, headers=None):
            asked.append(params["name"])
            if params["name"] == "firma-ornek.com":
                return FakeResponse({"Answer": [{"data": '"reconclaw-verify=abc"'}]})
            return FakeResponse({})

    assert asyncio.run(verify._check_dns(FakeClient(), "www.firma-ornek.com", "reconclaw-verify=abc")) is True
    assert asked == ["www.firma-ornek.com", "firma-ornek.com"]  # TLD'ye ("com") hiç sorulmaz
