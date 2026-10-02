"""
Bot koruması: kayıt ve giriş formları için iki katman.

  1. Cloudflare Turnstile (isteğe bağlı): .env dosyasında TURNSTILE_SITE_KEY ve TURNSTILE_SECRET_KEY
     tanımlıysa formda Cloudflare'in görünmez / tek tıklık doğrulaması çıkar. Sunucu her kayıt ve
     girişte jetonu Cloudflare'e doğrulatır; jetonsuz veya sahte istek reddedilir.
     Anahtarlar ücretsizdir: https://dash.cloudflare.com → Turnstile → Add widget
  2. Bal küpü (honeypot, her zaman açık): insanların görmediği gizli bir alan. Botlar formdaki
     her alanı doldurduğu için bu alan doluysa istek bot kabul edilir.

Bunlara ek olarak main.py'deki IP başına giriş / kayıt hız sınırı (5 dakikada 10 deneme) çalışır.
"""

import httpx

from core import config

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class CaptchaError(Exception):
    pass


def enabled() -> bool:
    return bool(config.TURNSTILE_SITE_KEY and config.TURNSTILE_SECRET_KEY)


async def check(token: str | None, honeypot: str | None, ip: str):
    if honeypot:
        raise CaptchaError("İstek doğrulanamadı.")
    if not enabled():
        return
    if not token:
        raise CaptchaError("Lütfen robot olmadığınızı doğrulayın.")
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            res = await client.post(VERIFY_URL, data={
                "secret": config.TURNSTILE_SECRET_KEY, "response": token[:2048], "remoteip": ip,
            })
            ok = res.json().get("success") is True
    except (httpx.HTTPError, ValueError):
        raise CaptchaError("Bot doğrulama servisine ulaşılamadı, birkaç saniye sonra tekrar deneyin.")
    if not ok:
        raise CaptchaError("Robot doğrulaması başarısız. Sayfayı yenileyip tekrar deneyin.")
