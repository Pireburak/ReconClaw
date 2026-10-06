import asyncio

import pytest

from core import config, plans, pricing


@pytest.fixture(autouse=True)
def fixed_rates(monkeypatch):
    monkeypatch.setattr(config, "FX_RATES", "EUR=52")
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


def test_turkey_pays_try_everyone_else_euro():
    assert pricing.region_of("TR")["currency"] == "TRY"
    for country in ("DE", "US", "SA", "GB", "BR", "JP"):
        assert pricing.region_of(country)["currency"] == "EUR"  # tek Euro hesabı
    de = pricing.region_of("DE")
    assert pricing.local_price(299, de) == 24.99           # (299 + 950) / 52 = 24.02 → 24,99 €
    assert pricing.local_price(299, de, yearly=True) == 249.9
    assert pricing.local_price(1999, pricing.region_of("US")) == 56.99  # (1999 + 950) / 52 = 56.7


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


def test_region_comes_only_from_ip(client, monkeypatch):
    data = client.get("/api/plans").json()
    assert data["detected"]["country"] == "TR" and data["pricing"]["currency"] == "TRY"
    assert data["pricing"]["prices"]["ultra_max"]["monthly"] == 1999
    assert "regions" not in data and "checkout_pricing" not in data

    async def from_germany(ip, headers):
        return "DE"

    monkeypatch.setattr(pricing, "detect_country", from_germany)
    # Almanya'dan gelen biri bölgeyi elle TR yapamaz: parametre yok sayılır, fiyat Euro kalır
    tricked = client.get("/api/plans?country=TR").json()
    assert tricked["pricing"]["currency"] == "EUR" and tricked["pricing"]["prices"]["pro"]["monthly"] == 24.99
    res = client.post("/api/billing/checkout", json={"plan": "pro", "country": "TR", "currency": "TRY"}).json()
    assert res["currency"] == "EUR" and res["amount"] == 24.99
    assert 'id="regionSelect"' not in client.get("/").text


def test_unknown_country_blocks_payment_instead_of_tl(client, monkeypatch):
    async def unknown(ip, headers):
        return None

    monkeypatch.setattr(pricing, "detect_country", unknown)
    res = client.post("/api/billing/checkout", json={"plan": "pro"})
    assert res.status_code == 503 and "belirlenemedi" in res.json()["detail"]
    assert client.get("/api/me").json()["subscription"]["plan"]["id"] == "free"


def test_geo_lookup_falls_back_and_never_caches_failure(monkeypatch):
    monkeypatch.setattr(config, "GEO_LOOKUP", True)
    monkeypatch.setattr(config, "TRUST_COUNTRY_HEADER", False)
    pricing._geo_cache.clear()
    calls = []

    class FakeResponse:
        def __init__(self, status, text="", data=None):
            self.status_code, self.text, self._data = status, text, data

        def json(self):
            return self._data

    responses = {"ipapi.co": FakeResponse(429, "RateLimited"), "country.is": FakeResponse(200, data={"country": "de"})}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url):
            calls.append(url)
            for host, response in responses.items():
                if host in url:
                    return response
            return FakeResponse(500)

    monkeypatch.setattr(pricing.httpx, "AsyncClient", FakeClient)
    assert asyncio.run(pricing.detect_country("8.8.4.4", {})) == "DE"  # ilk servis sınırda, ikincisi cevapladı
    responses.clear()
    assert asyncio.run(pricing.detect_country("1.1.1.1", {})) is None    # hepsi düştü: TR varsayılmaz
    assert "1.1.1.1" not in pricing._geo_cache
    assert pricing.region_of(None)["unknown"] is True


def test_checkout_charges_detected_region_not_preview(client, monkeypatch):
    async def from_saudi(ip, headers):
        return "SA"

    monkeypatch.setattr(pricing, "detect_country", from_saudi)
    res = client.post("/api/billing/checkout", json={"plan": "pro", "period": "monthly"}).json()
    assert res["currency"] == "EUR" and res["country"] == "SA"  # Suudi Arabistan'dan bile Euro
    assert res["amount"] == 24.99
    assert res["amount_try"] == pricing.to_try(24.99, "EUR")
    pay = client.get("/api/billing").json()["payments"][0]
    assert pay["currency"] == "EUR" and pay["country"] == "SA"
