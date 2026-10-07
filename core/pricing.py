"""
Bölgeye göre fiyatlandırma: Türkiye'den gelen ziyaretçiler TL, yurt dışından gelenler Euro öder.

  * Türkiye'de fiyatlar plan tablosundaki gibidir (TL) ve her zaman en ucuzu Türkiye'dir.
  * Yurt dışında (Türkiye dışındaki tüm ülkeler) her ücretli planın aylık fiyatına
    REGIONAL_SURCHARGE_TRY (varsayılan 950 TL) eklenir ve güncel Euro kuruyla çevrilir; sonuç
    x,99 biçimine yuvarlanır. Yıllık fiyat = aylık × 10. Tek bir Euro hesabıyla tahsilat yapılabilir.
  * Site Cloudflare arkasındaysa sunucuya gelen IP Cloudflare'in (çoğu yurt dışında) sunucusudur.
    İstek gerçekten bir Cloudflare IP'sinden geliyorsa Cloudflare'in CF-IPCountry / CF-Connecting-IP
    başlıkları otomatik kullanılır (ayar gerekmez; başka yerden gelen istekte bu başlıklar yok sayılır).
  * Bölge YALNIZCA IP adresinden belirlenir; kullanıcı seçemez (aksi halde herkes TL seçerdi).
    Sıra: (isteğe bağlı) Cloudflare'in CF-IPCountry başlığı → istemci IP'si için çevrimiçi GeoIP
    servisleri (ipapi.co, country.is, ipwho.is; biri cevap vermezse sıradaki) → hepsi başarısızsa
    ülke "bilinmiyor" sayılır ve ödeme başlatılmaz (varsayılan TL'ye düşülmez). Yerel ağ adresleri
    (127.0.0.1, 192.168.x) ve GEO_LOOKUP kapalıyken DEFAULT_COUNTRY kullanılır.
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
# Sırayla denenir; ilk geçerli iki harfli ülke kodu kullanılır
GEO_PROVIDERS = (
    ("https://ipapi.co/{ip}/country/", None),          # düz metin: "DE"
    ("https://api.country.is/{ip}", "country"),        # {"country": "DE"}
    ("https://ipwho.is/{ip}?fields=country_code", "country_code"),
)
RATES_TTL = 12 * 3600

# Cloudflare'in vekil sunucu adresleri (https://www.cloudflare.com/ips/). Yalnızca bu adreslerden gelen
# isteklerde CF-IPCountry / CF-Connecting-IP başlıklarına güvenilir; ek aralık için CLOUDFLARE_EXTRA_IPS.
CLOUDFLARE_RANGES = (
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
    "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
    "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22",
    "2400:cb00::/32", "2606:4700::/32", "2803:f800::/32", "2405:b500::/32", "2405:8100::/32",
    "2a06:98c0::/29", "2c0f:f248::/32",
)
_CF_NETS = None

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
    """Ülkenin para birimi. country None ise (tespit edilemedi) gösterim için varsayılan ülke kullanılır,
    ama bölge "unknown" olarak işaretlenir ve ödeme başlatılmaz."""
    unknown = country is None
    country = (country or config.DEFAULT_COUNTRY).upper()
    currency, name = COUNTRIES.get(country, DEFAULT_FOREIGN)
    return {"country": country, "currency": currency, "name": name, "unknown": unknown}


def is_cloudflare(ip: str) -> bool:
    """Bağlantı bir Cloudflare vekil sunucusundan mı geliyor?"""
    global _CF_NETS
    if _CF_NETS is None:
        extra = [x.strip() for x in config.env("CLOUDFLARE_EXTRA_IPS").split(",") if x.strip()]
        _CF_NETS = [ipaddress.ip_network(n, strict=False) for n in (*CLOUDFLARE_RANGES, *extra)]
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _CF_NETS)


def real_ip(peer_ip: str, headers) -> str:
    """Ziyaretçinin gerçek IP'si: Cloudflare'den geliyorsa (veya TRUST_PROXY_IP açıksa) CF-Connecting-IP."""
    if config.TRUST_PROXY_IP or is_cloudflare(peer_ip):
        forwarded = (headers.get("cf-connecting-ip") or "").strip()
        try:
            return str(ipaddress.ip_address(forwarded))
        except ValueError:
            pass
    return peer_ip


def _valid(code) -> str | None:
    code = str(code or "").strip().upper()
    return code if len(code) == 2 and code.isalpha() and code not in ("XX", "T1") else None


async def _lookup(ip: str) -> str | None:
    async with httpx.AsyncClient(timeout=3) as client:
        for url, key in GEO_PROVIDERS:
            try:
                res = await client.get(url.format(ip=ip))
                if res.status_code != 200:
                    continue
                code = _valid(res.text if key is None else res.json().get(key))
                if code:
                    return code
            except (httpx.HTTPError, ValueError, AttributeError):
                continue
    return None


async def detect_country(ip: str, headers, peer_ip: str | None = None) -> str | None:
    """Ziyaretçinin ülkesi. ip: gerçek ziyaretçi IP'si, peer_ip: sunucuya bağlanan adres (Cloudflare olabilir).
    Hiçbir kaynak cevap vermezse None (bilinmiyor) döner; sonuç önbelleğe alınmaz."""
    if config.TRUST_COUNTRY_HEADER or is_cloudflare(peer_ip or ip):
        header = _valid(headers.get("cf-ipcountry"))  # T1 = Tor, XX = bilinmiyor
        if header:
            return header
    try:
        if not ipaddress.ip_address(ip).is_global:
            return config.DEFAULT_COUNTRY
    except ValueError:
        return config.DEFAULT_COUNTRY
    if is_cloudflare(ip):
        return None  # gerçek IP bilinmiyor: Cloudflare sunucusunun ülkesi ziyaretçinin ülkesi değildir
    if not config.GEO_LOOKUP:
        return config.DEFAULT_COUNTRY
    if ip in _geo_cache:
        return _geo_cache[ip]
    country = await _lookup(ip)
    if country is None:
        return None  # önbelleğe alma: bir sonraki istekte tekrar denenir
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
