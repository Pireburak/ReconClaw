"""
Bölgeye göre fiyatlandırma: Türkiye'den gelen ziyaretçiler TL, yurt dışından gelenler Euro öder.

  * Türkiye'de fiyatlar plan tablosundaki gibidir (TL) ve her zaman en ucuzu Türkiye'dir.
  * Yurt dışında (Türkiye dışındaki tüm ülkeler) her ücretli planın aylık fiyatına
    REGIONAL_SURCHARGE_TRY (varsayılan 950 TL) eklenir ve güncel Euro kuruyla çevrilir; sonuç
    x,99 biçimine yuvarlanır. Yıllık fiyat = aylık × 10. Tek bir Euro hesabıyla tahsilat yapılabilir.
  * Ülke tespiti: (isteğe bağlı) Cloudflare'in CF-IPCountry başlığı → istemci IP'si için
    çevrimiçi GeoIP sorgusu (önbellekli) → bulunamazsa DEFAULT_COUNTRY (TR). Yerel ağ adresleri
    (127.0.0.1, 192.168.x) her zaman varsayılan ülkeye düşer.
  * Euro kuru open.er-api.com'dan 12 saatte bir alınır; internet yoksa .env'deki FX_RATES veya
    yerleşik yaklaşık kur kullanılır.
"""

import ipaddress
import math
import time

import httpx

from core import config

# Türkiye TL öder; diğer tüm ülkeler Euro öder
COUNTRIES = {"TR": ("TRY", "Türkiye")}
DEFAULT_FOREIGN = ("EUR", "Yurt dışı")

# 1 birim yabancı para = kaç TL (yalnızca çevrimdışı yedek; YAKLAŞIK değerlerdir, canlı kur tercih edilir)
FALLBACK_TRY_PER_UNIT = {"EUR": 52.0}

RATES_URL = "https://open.er-api.com/v6/latest/TRY"
GEO_URL = "https://ipapi.co/{ip}/country/"
RATES_TTL = 12 * 3600

_rates = {"at": 0.0, "try_per_unit": {}, "source": "yedek", "updated": None}
_geo_cache: dict[str, str] = {}


# ---------------------------------------------------------------- kurlar
def _env_rates() -> dict:
    out = {}
    for part in config.FX_RATES.split(","):
        if "=" in part:
            code, value = part.split("=", 1)
            try:
                out[code.strip().upper()] = float(value)
            except ValueError:
                pass
    return out


async def refresh_rates(force: bool = False) -> dict:
    """Güncel kurları çeker (12 saat önbellek). Hata olursa yedek kurlar kalır."""
    if not force and _rates["try_per_unit"] and time.time() - _rates["at"] < RATES_TTL:
        return _rates
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            data = (await client.get(RATES_URL)).json()
        per_try = data["rates"]  # 1 TL = x birim
        _rates.update(try_per_unit={c: 1 / v for c, v in per_try.items() if v}, source="open.er-api.com",
                      updated=data.get("time_last_update_utc"), at=time.time())
    except (httpx.HTTPError, ValueError, KeyError, TypeError, ZeroDivisionError):
        _rates["at"] = time.time() - RATES_TTL + 600  # 10 dk sonra tekrar dene
    return _rates


def try_per_unit(currency: str) -> tuple[float, str]:
    """1 birim yabancı paranın TL karşılığı ve kaynağı."""
    env = _env_rates()
    if currency in env:
        return env[currency], ".env"
    if currency in _rates["try_per_unit"]:
        return _rates["try_per_unit"][currency], _rates["source"]
    return FALLBACK_TRY_PER_UNIT.get(currency, FALLBACK_TRY_PER_UNIT["EUR"]), "yaklaşık (çevrimdışı)"


# ---------------------------------------------------------------- ülke tespiti
def region_of(country: str | None) -> dict:
    country = (country or config.DEFAULT_COUNTRY).upper()
    currency, name = COUNTRIES.get(country, DEFAULT_FOREIGN)
    return {"country": country, "currency": currency, "name": name}


async def detect_country(ip: str, headers) -> str:
    if config.TRUST_COUNTRY_HEADER:
        header = (headers.get("cf-ipcountry") or "").strip().upper()
        if len(header) == 2 and header.isalpha() and header != "XX":
            return header
    try:
        if not ipaddress.ip_address(ip).is_global:
            return config.DEFAULT_COUNTRY
    except ValueError:
        return config.DEFAULT_COUNTRY
    if ip in _geo_cache:
        return _geo_cache[ip]
    country = config.DEFAULT_COUNTRY
    if config.GEO_LOOKUP:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                text = (await client.get(GEO_URL.format(ip=ip))).text.strip().upper()
            if len(text) == 2 and text.isalpha():
                country = text
        except httpx.HTTPError:
            pass
    if len(_geo_cache) > 5000:
        _geo_cache.clear()
    _geo_cache[ip] = country
    return country


# ---------------------------------------------------------------- fiyatlar
def _price_tag(value: float, currency: str) -> float:
    """Yerel fiyatı x,99 biçimine yuvarlar (ör. 24,02 € → 24,99 €)."""
    return math.ceil(value) - 0.01


def local_price(price_try: int, region: dict, yearly: bool = False) -> float:
    """TL plan fiyatını bölgenin para birimine çevirir. Türkiye'de fiyat aynen kalır."""
    if not price_try:
        return 0
    if region["currency"] == "TRY":
        return price_try * (10 if yearly else 1)
    rate, _ = try_per_unit(region["currency"])
    monthly = _price_tag((price_try + config.REGIONAL_SURCHARGE_TRY) / rate, region["currency"])
    return round(monthly * 10, 2) if yearly else monthly


def to_try(amount: float, currency: str) -> int:
    if currency == "TRY":
        return int(round(amount))
    return int(round(amount * try_per_unit(currency)[0]))


def price_list(plans, region: dict) -> dict:
    rate, source = try_per_unit(region["currency"]) if region["currency"] != "TRY" else (1.0, "—")
    return {
        **region,
        "rate": rate, "rate_source": source, "rates_updated": _rates["updated"],
        "surcharge_try": 0 if region["currency"] == "TRY" else config.REGIONAL_SURCHARGE_TRY,
        "prices": {p.id: {"monthly": local_price(p.price_monthly, region),
                          "yearly": local_price(p.price_monthly, region, yearly=True)} for p in plans},
    }


def supported_regions() -> list:
    """Önizleme menüsü: Türkiye (TL) ve yurt dışı (Euro)."""
    return [{"country": "TR", "currency": "TRY", "name": "Türkiye"}, {"country": "EU", "currency": "EUR", "name": "Yurt dışı"}]
