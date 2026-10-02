import asyncio

import pytest

from core import config, plans, pricing


@pytest.fixture(autouse=True)
def fixed_rates(monkeypatch):
    monkeypatch.setattr(config, "FX_RATES", "USD=45,EUR=52,SAR=12,GBP=60")
    monkeypatch.setattr(config, "REGIONAL_SURCHARGE_TRY", 950)


def test_turkey_keeps_try_prices_and_is_cheapest():
    tr = pricing.region_of("TR")
    assert pricing.local_price(1999, tr) == 1999 and pricing.local_price(1999, tr, yearly=True) == 19990
    for country in ("DE", "US", "SA", "GB", "BR"):
        region = pricing.region_of(country)
        for plan in plans.PLANS.values():
            local = pricing.local_price(plan.price_monthly, region)
            if not plan.price_monthly:
                assert local == 0
                continue
            in_try = pricing.to_try(local, region["currency"])
            # Yurt dışı fiyatı TL karşılığı: plan fiyatı + yaklaşık 950 TL (yuvarlama payıyla)
            assert plan.price_monthly + 900 <= in_try <= plan.price_monthly + 1000 + pricing.try_per_unit(region["currency"])[0]


def test_currency_by_country_and_price_tags():
    assert pricing.region_of("DE")["currency"] == "EUR"
    assert pricing.region_of("US")["currency"] == "USD"
    assert pricing.region_of("SA")["currency"] == "SAR"
    assert pricing.region_of("BR")["currency"] == "USD"  # listede olmayan ülke → dolar
    de = pricing.region_of("DE")
    assert pricing.local_price(299, de) == 24.99           # (299 + 950) / 52 = 24.02 → 24,99 €
    assert pricing.local_price(299, de, yearly=True) == 249.9
    assert pricing.local_price(1999, pricing.region_of("US")) == 65.99  # (1999 + 950) / 45 = 65.5


def test_country_detection(monkeypatch):
    monkeypatch.setattr(config, "GEO_LOOKUP", False)
    assert asyncio.run(pricing.detect_country("127.0.0.1", {})) == "TR"
    assert asyncio.run(pricing.detect_country("192.168.1.5", {"cf-ipcountry": "DE"})) == "TR"  # başlığa güvenilmiyor
    monkeypatch.setattr(config, "TRUST_COUNTRY_HEADER", True)
    assert asyncio.run(pricing.detect_country("8.8.8.8", {"cf-ipcountry": "de"})) == "DE"


pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    from core import db_manager

    monkeypatch.setattr(db_manager, "DB_PATH", str(tmp_path / "pricing.db"))
    import main

    with TestClient(main.app) as c:
        c.post("/auth/register", json={"email": "bolge@example.com", "password": "parola123"})
        yield c


def test_plans_endpoint_detects_region_and_previews(client):
    data = client.get("/api/plans").json()
    assert data["detected"]["country"] == "TR" and data["pricing"]["currency"] == "TRY"
    assert data["pricing"]["prices"]["ultra_max"]["monthly"] == 1999
    preview = client.get("/api/plans?country=DE").json()
    assert preview["pricing"]["currency"] == "EUR" and preview["detected"]["country"] == "TR"
    assert preview["pricing"]["prices"]["pro"]["monthly"] == 24.99
    assert any(r["country"] == "SA" for r in preview["regions"])


def test_checkout_charges_detected_region_not_preview(client, monkeypatch):
    async def from_saudi(ip, headers):
        return "SA"

    monkeypatch.setattr(pricing, "detect_country", from_saudi)
    res = client.post("/api/billing/checkout", json={"plan": "pro", "period": "monthly"}).json()
    assert res["currency"] == "SAR" and res["country"] == "SA"
    assert res["amount"] == pricing.local_price(299, pricing.region_of("SA"))  # (299+950)/12 → 104,99 SAR
    assert res["amount_try"] == pricing.to_try(res["amount"], "SAR")
    pay = client.get("/api/billing").json()["payments"][0]
    assert pay["currency"] == "SAR" and pay["country"] == "SA"
