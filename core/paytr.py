"""
PayTR iFrame API ile gerçek ödeme.

Akış:
  1. Kullanıcı plan seçer → sunucu "pending" durumlu bir sipariş (merchant_oid) oluşturur ve
     PayTR'den bir iFrame jetonu alır (get-token). Kart bilgisi ReconClaw'a hiç gelmez;
     kullanıcı kartını PayTR'nin güvenli iFrame'ine girer.
  2. Ödeme bitince PayTR, panelde tanımlı Bildirim URL'sine (…/odeme/paytr/bildirim) sunucudan
     sunucuya POST atar. İmza (hash) doğrulanır, tutar kontrol edilir ve plan etkinleşir.
     PayTR yalnızca düz metin "OK" yanıtını kabul eder; başka yanıtta bildirimi tekrarlar.
  3. Kullanıcının tarayıcısı merchant_ok_url / merchant_fail_url adresine döner. Bu adres ödemenin
     kanıtı DEĞİLDİR; planı yalnızca imzası doğrulanmış bildirim etkinleştirir.

İmzalar: base64( HMAC-SHA256( merchant_key, alanlar + merchant_salt ) )
  get-token: merchant_id + user_ip + merchant_oid + email + payment_amount + user_basket
             + no_installment + max_installment + currency + test_mode
  bildirim : merchant_oid + merchant_salt + status + total_amount
"""

import base64
import hashlib
import hmac
import json
import logging

import httpx

from core import config

log = logging.getLogger("reconclaw.paytr")

TOKEN_URL = "https://www.paytr.com/odeme/api/get-token"
IFRAME_BASE = "https://www.paytr.com/odeme/guvenli/"
RESIZER_JS = "https://www.paytr.com/js/iframeResizer.min.js"
ORIGIN = "https://www.paytr.com"


class PaymentError(Exception):
    pass


def enabled() -> bool:
    return bool(config.PAYTR_MERCHANT_ID and config.PAYTR_MERCHANT_KEY and config.PAYTR_MERCHANT_SALT)


def _sign(message: str) -> str:
    digest = hmac.new(config.PAYTR_MERCHANT_KEY.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _currency(code: str) -> str:
    return "TL" if code == "TRY" else code  # PayTR TL / EUR / USD / GBP / RUB bekler


def basket(name: str, amount: float) -> str:
    return base64.b64encode(json.dumps([[name, f"{amount:.2f}", 1]], ensure_ascii=False).encode()).decode()


def token_fields(*, merchant_oid: str, email: str, amount: float, currency: str, user_ip: str,
                 item_name: str, user_name: str, ok_url: str, fail_url: str) -> dict:
    """get-token isteğinin form alanlarını ve imzasını üretir (ağ çağrısı yapmaz; testlenebilir)."""
    payment_amount = str(int(round(amount * 100)))  # kuruş / cent
    user_basket = basket(item_name, amount)
    no_installment, max_installment = "1", "0"     # abonelikte taksit kapalı
    cur = _currency(currency)
    test_mode = "1" if config.PAYTR_TEST_MODE else "0"
    hash_str = (f"{config.PAYTR_MERCHANT_ID}{user_ip}{merchant_oid}{email}{payment_amount}{user_basket}"
                f"{no_installment}{max_installment}{cur}{test_mode}")
    return {
        "merchant_id": config.PAYTR_MERCHANT_ID,
        "user_ip": user_ip,
        "merchant_oid": merchant_oid,
        "email": email,
        "payment_amount": payment_amount,
        "paytr_token": _sign(hash_str + config.PAYTR_MERCHANT_SALT),
        "user_basket": user_basket,
        "debug_on": "1" if config.PAYTR_TEST_MODE else "0",
        "no_installment": no_installment,
        "max_installment": max_installment,
        "user_name": (user_name or email)[:60],
        "user_address": config.PAYTR_DEFAULT_ADDRESS,
        "user_phone": config.PAYTR_DEFAULT_PHONE,
        "merchant_ok_url": ok_url,
        "merchant_fail_url": fail_url,
        "timeout_limit": "30",
        "currency": cur,
        "test_mode": test_mode,
        "lang": "tr",
    }


async def get_iframe_url(fields: dict) -> str:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(TOKEN_URL, data=fields)
            data = res.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("PayTR get-token başarısız: %s", exc)
        raise PaymentError("Ödeme sağlayıcısına ulaşılamadı. Birkaç dakika sonra tekrar deneyin.")
    if data.get("status") != "success" or not data.get("token"):
        log.warning("PayTR get-token reddetti: %s", data.get("reason"))
        raise PaymentError(f"Ödeme başlatılamadı: {data.get('reason') or 'bilinmeyen hata'}")
    return IFRAME_BASE + data["token"]


def verify_callback(form: dict) -> bool:
    """Bildirimin gerçekten PayTR'den geldiğini imzasıyla doğrular."""
    try:
        expected = _sign(f"{form['merchant_oid']}{config.PAYTR_MERCHANT_SALT}{form['status']}{form['total_amount']}")
        return hmac.compare_digest(expected.encode(), str(form["hash"]).encode())
    except KeyError:
        return False
