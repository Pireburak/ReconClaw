import base64
import hashlib
import hmac
import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from core import auth, config, mailer, paytr, plans  # noqa: E402

KEY, SALT = "test-key-123", "test-salt-456"


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "pay.db"))
    monkeypatch.setattr(config, "PAYTR_MERCHANT_ID", "123456")
    monkeypatch.setattr(config, "PAYTR_MERCHANT_KEY", KEY)
    monkeypatch.setattr(config, "PAYTR_MERCHANT_SALT", SALT)
    monkeypatch.setattr(config, "PAYTR_TEST_MODE", True)
    monkeypatch.setattr(config, "GEO_LOOKUP", False)
    monkeypatch.setattr(config, "DEFAULT_COUNTRY", "TR")
    import main

    with TestClient(main.app) as c:
        c.post("/auth/register", json={"email": "alici@example.com", "password": "parola123"})
        yield c


def sign(msg: str) -> str:
    return base64.b64encode(hmac.new(KEY.encode(), msg.encode(), hashlib.sha256).digest()).decode()


def notify(client, oid, status="success", amount="29900", test_mode="1"):
    form = {"merchant_oid": oid, "status": status, "total_amount": amount, "payment_amount": amount,
            "hash": sign(f"{oid}{SALT}{status}{amount}"), "test_mode": test_mode,
            "failed_reason_code": "" if status == "success" else "2", "failed_reason_msg": ""}
    return client.post("/odeme/paytr/bildirim", data=form)


def start_checkout(client, monkeypatch, plan="pro"):
    captured = {}

    async def fake_iframe(fields):
        captured.update(fields)
        return paytr.IFRAME_BASE + "TOKEN"

    monkeypatch.setattr(paytr, "get_iframe_url", fake_iframe)
    res = client.post("/api/billing/checkout", json={"plan": plan, "accept_terms": True})
    assert res.status_code == 200, res.text
    return res.json(), captured


def test_token_hash_matches_paytr_spec(client):
    fields = paytr.token_fields(merchant_oid="RC1T1ABC", email="a@b.com", amount=299, currency="TRY",
                                user_ip="1.2.3.4", item_name="ReconClaw Pro", user_name="John Doe",
                                ok_url="https://x/ok", fail_url="https://x/fail")
    assert fields["payment_amount"] == "29900" and fields["currency"] == "TL" and fields["test_mode"] == "1"
    assert json.loads(base64.b64decode(fields["user_basket"])) == [["ReconClaw Pro", "299.00", 1]]
    expected = sign("123456" "1.2.3.4" "RC1T1ABC" "a@b.com" "29900" + fields["user_basket"] + "1" "0" "TL" "1" + SALT)
    assert fields["paytr_token"] == expected


def test_checkout_requires_terms_and_does_not_activate(client, monkeypatch):
    res = client.post("/api/billing/checkout", json={"plan": "pro"})
    assert res.status_code == 400 and "Sözleşme" in res.json()["detail"]
    data, fields = start_checkout(client, monkeypatch)
    assert data["mode"] == "paytr" and data["iframe_url"].endswith("/TOKEN")
    assert fields["merchant_ok_url"].endswith("/odeme/sonuc?durum=basarili")
    assert fields["merchant_oid"].isalnum() and len(fields["merchant_oid"]) <= 64
    # Ödeme onaylanana kadar plan değişmez
    assert client.get("/api/me").json()["subscription"]["plan"]["id"] == "free"
    pays = client.get("/api/billing").json()["payments"]
    assert pays[0]["status"] == "pending" and pays[0]["merchant_oid"] == data["merchant_oid"]
    assert client.get("/api/plans").json()["payment_mode"] == "paytr"


def test_callback_activates_plan_once(client, monkeypatch):
    data, _ = start_checkout(client, monkeypatch)
    oid = data["merchant_oid"]
    res = notify(client, oid)
    assert res.status_code == 200 and res.text == "OK"
    sub = client.get("/api/me").json()["subscription"]
    assert sub["plan"]["id"] == "pro"
    first_expiry = sub["expires"]
    # PayTR aynı bildirimi tekrarlayabilir: süre ikinci kez uzatılmaz
    assert notify(client, oid).text == "OK"
    assert client.get("/api/me").json()["subscription"]["expires"] == first_expiry
    assert client.get("/api/billing").json()["payments"][0]["status"] == "paid"


def test_callback_rejects_bad_hash_and_wrong_amount(client, monkeypatch):
    data, _ = start_checkout(client, monkeypatch)
    oid = data["merchant_oid"]
    forged = {"merchant_oid": oid, "status": "success", "total_amount": "29900", "hash": "sahte"}
    assert client.post("/odeme/paytr/bildirim", data=forged).status_code == 400
    assert notify(client, oid, amount="100").text == "OK"  # imzalı ama eksik tutar
    assert client.get("/api/me").json()["subscription"]["plan"]["id"] == "free"
    assert client.get("/api/billing").json()["payments"][0]["status"] == "failed"


def test_failed_payment_and_live_mode_ignores_test_callbacks(client, monkeypatch):
    data, _ = start_checkout(client, monkeypatch)
    assert notify(client, data["merchant_oid"], status="failed").text == "OK"
    assert client.get("/api/billing").json()["payments"][0]["status"] == "failed"
    monkeypatch.setattr(config, "PAYTR_TEST_MODE", False)
    data, _ = start_checkout(client, monkeypatch)
    assert notify(client, data["merchant_oid"], test_mode="1").text == "OK"
    assert client.get("/api/me").json()["subscription"]["plan"]["id"] == "free"


def test_renewal_extends_remaining_time(client, monkeypatch):
    data, _ = start_checkout(client, monkeypatch)
    notify(client, data["merchant_oid"])
    first = client.get("/api/me").json()["subscription"]["expires"]
    data, _ = start_checkout(client, monkeypatch)
    notify(client, data["merchant_oid"])
    second = client.get("/api/me").json()["subscription"]["expires"]
    from datetime import datetime
    assert (datetime.fromisoformat(second) - datetime.fromisoformat(first)).days == 30


def test_result_page_is_frameable_only_by_self(client):
    res = client.get("/odeme/sonuc?durum=basarili")
    assert res.status_code == 200 and "frame-ancestors 'self'" in res.headers["content-security-policy"]
    assert "/?odeme=basarili#plans" in res.text
    main_csp = client.get("/login").headers["content-security-policy"]
    assert "frame-ancestors 'none'" in main_csp


def test_public_and_legal_pages(client, monkeypatch):
    monkeypatch.setattr(config, "COMPANY_TITLE", "John Doe Yazılım")
    monkeypatch.setattr(config, "COMPANY_EMAIL", "destek@example.com")
    client.cookies.clear()
    for slug in ("mesafeli-satis", "on-bilgilendirme", "iade", "kvkk", "gizlilik", "kullanim"):
        res = client.get(f"/yasal/{slug}")
        assert res.status_code == 200 and "John Doe Yazılım" in res.text
    assert client.get("/yasal/yok").status_code == 404
    pricing = client.get("/fiyatlandirma").text
    assert "Ultra Max" in pricing and "₺1.999" in pricing and "Admin" not in pricing
    assert "destek@example.com" in client.get("/iletisim").text
    login = client.get("/login").text
    assert "/yasal/mesafeli-satis" in login and "acceptTerms" in login
    assert "Disallow: /api/" in client.get("/robots.txt").text
    assert "mailto:destek@example.com" in client.get("/.well-known/security.txt").text


def test_register_rejects_unaccepted_terms(client):
    client.cookies.clear()
    res = client.post("/auth/register", json={"email": "red@example.com", "password": "parola123", "accept_terms": False})
    assert res.status_code == 400


def test_password_reset_flow(client, monkeypatch):
    sent = []
    monkeypatch.setattr(config, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(config, "SMTP_FROM", "no-reply@example.com")
    monkeypatch.setattr(mailer, "send", lambda to, subject, text: sent.append((to, text)) or True)
    client.cookies.clear()
    assert client.get("/sifremi-unuttum").status_code == 200
    # Var olmayan hesap için de aynı yanıt (hesap varlığı sızmaz), e-posta gitmez
    unknown = client.post("/auth/forgot", json={"email": "yok@example.com"}).json()
    known = client.post("/auth/forgot", json={"email": "alici@example.com"}).json()
    assert unknown == known and len(sent) == 1
    token = sent[0][1].split("/sifre-sifirla?t=")[1].split()[0]
    assert client.post("/auth/reset", json={"token": token, "password": "YeniParola99"}).status_code == 200
    # Tek kullanımlık
    assert client.post("/auth/reset", json={"token": token, "password": "BaskaParola99"}).status_code == 400
    assert client.post("/auth/login", json={"email": "alici@example.com", "password": "YeniParola99"}).status_code == 200


def test_forgot_hidden_without_smtp(client, monkeypatch):
    monkeypatch.setattr(config, "SMTP_HOST", "")
    client.cookies.clear()
    assert client.post("/auth/forgot", json={"email": "alici@example.com"}).status_code == 404
    assert "Şifremi unuttum" not in client.get("/login").text


def test_client_ip_uses_cloudflare_header_only_when_trusted(client, monkeypatch):
    import main
    from starlette.requests import Request

    req = Request({"type": "http", "headers": [(b"cf-connecting-ip", b"203.0.113.9")], "client": ("10.0.0.1", 1)})
    monkeypatch.setattr(config, "TRUST_PROXY_IP", False)
    assert main.client_ip(req) == "10.0.0.1"
    monkeypatch.setattr(config, "TRUST_PROXY_IP", True)
    assert main.client_ip(req) == "203.0.113.9"


def test_admin_revenue_counts_only_paid(client, monkeypatch):
    from core import admin

    data, _ = start_checkout(client, monkeypatch)  # pending
    assert admin.overview()["payments_total"] == 0
    notify(client, data["merchant_oid"])
    assert admin.overview()["payments_total"] == 1 and admin.overview()["revenue_total"] == 299
    assert plans.payments(auth.user_by_email("alici@example.com")["id"])[0]["status"] == "paid"
