"""
Hedef sahipliği doğrulama.

ReconClaw internette yayındayken birinin, sahibi olmadığı bir sistemi taramasını önlemek için
`REQUIRE_TARGET_VERIFICATION=true` ile yalnızca doğrulanmış hedeflerin taranmasına izin verilir.
Kullanıcı, hedefin kendisine ait olduğunu iki yoldan biriyle kanıtlar:

  1. DNS:   alan adına  TXT  "reconclaw-verify=<anahtar>"  kaydı ekler
  2. Dosya: http(s)://<hedef>/.well-known/reconclaw-verify.txt  dosyasına anahtarı yazar

DNS sorgusu ek bağımlılık gerektirmemek için DNS-over-HTTPS (Cloudflare) ile yapılır.
"""

import ipaddress
import secrets
import socket
from contextlib import closing
from datetime import datetime

import httpx

from core import config
from core.db_manager import get_db_connection
from core.engine import normalize_target
from core.plans import UNLIMITED, PlanError, effective_plan

TOKEN_PREFIX = "reconclaw-verify="
WELL_KNOWN = "/.well-known/reconclaw-verify.txt"
DOH_URL = "https://cloudflare-dns.com/dns-query"
# Sahipleri tarafından herkese açık biçimde "beni tarayın / test edin" denilen, taranması serbest
# test sunucuları. Doğrulama gerektirmeden taranabilir (sunum ve deneme için). Kaynaklar:
#   scanme.nmap.org           -> Nmap projesinin resmî test sunucusu (nmap.org)
#   *.vulnweb.com             -> Acunetix'in bilerek zafiyetli bıraktığı herkese açık test siteleri
#   demo.testfire.net         -> IBM AltoroMutual örnek (test) bankası
#   badssl.com                -> TLS/sertifika test siteleri
# Ek olarak sunucu sahibi, yazılı izin aldığı hedefleri TEST_TARGETS ortam değişkeniyle ekleyebilir.
_BUILTIN_TEST_TARGETS = {
    "scanme.nmap.org",
    "testphp.vulnweb.com", "testasp.vulnweb.com", "testaspnet.vulnweb.com", "testhtml5.vulnweb.com",
    "rest.vulnweb.com", "demo.testfire.net", "badssl.com",
}
ALWAYS_ALLOWED = _BUILTIN_TEST_TARGETS | {
    normalize_target(h) for h in config.env("TEST_TARGETS").replace(";", ",").split(",") if h.strip()
}


class VerifyError(Exception):
    pass


# ---------------------------------------------------------------- kurumsal e-posta ile alan adı yetkisi
# Doğrulanmış kurumsal e-postası olan kullanıcı (ali@firma.com) kendi şirketinin alan adını (firma.com)
# DNS kaydı eklemeden hedef olarak ekleyebilir. Kişisel e-posta sağlayıcıları ve kamu / eğitim / askeri
# alan adları bu yoldan açılamaz: oralarda e-posta adresi, alan adının yetkilisi olmayı kanıtlamaz.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "outlook.com.tr", "hotmail.com", "hotmail.com.tr",
    "live.com", "msn.com", "yahoo.com", "yahoo.com.tr", "ymail.com", "icloud.com", "me.com", "mac.com",
    "aol.com", "yandex.com", "yandex.com.tr", "yandex.ru", "mail.ru", "proton.me", "protonmail.com",
    "pm.me", "gmx.com", "gmx.de", "gmx.net", "web.de", "zoho.com", "tutanota.com", "tuta.io",
    "mynet.com", "superonline.com", "ttmail.com", "hushmail.com", "fastmail.com", "qq.com", "163.com",
}
RESTRICTED_LABELS = {"gov", "edu", "mil", "ac", "k12", "pol", "bel", "tsk", "int"}


def email_domain_status(user) -> dict:
    """Kullanıcının e-posta alan adı, kurumsal yetki için uygun mu ve hedeflerine eklenmiş mi?"""
    email = (user["email"] or "").strip().lower()
    domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    labels = domain.split(".")
    status = {"email": email, "domain": domain, "verified": bool(user["email_verified"]),
              "eligible": False, "claimed": False, "reason": ""}
    if not domain or len(labels) < 2:
        status["reason"] = "invalid"
    elif domain in FREE_MAIL_DOMAINS:
        status["reason"] = "free_mail"
    elif labels[-1] in RESTRICTED_LABELS or labels[-2] in RESTRICTED_LABELS:
        status["reason"] = "restricted"
    else:
        status["eligible"] = True
    if domain:
        with closing(get_db_connection()) as conn:
            status["claimed"] = conn.execute(
                "SELECT 1 FROM targets WHERE user_id = ? AND host = ? AND method = 'email' AND verified_at IS NOT NULL",
                (user["id"], domain)).fetchone() is not None
    return status


def claim_email_domain(user) -> dict:
    """Doğrulanmış kurumsal e-postanın alan adını doğrulanmış hedef olarak ekler (alt alan adları dahil)."""
    st = email_domain_status(user)
    if not st["eligible"]:
        raise VerifyError({
            "free_mail": "Kişisel e-posta adresleriyle (gmail, outlook vb.) alan adı yetkisi alınamaz. "
                         "Kurumsal e-postanızla kayıt olun ya da DNS TXT kaydıyla doğrulayın.",
            "restricted": "Kamu, eğitim ve askeri alan adları e-posta ile doğrulanamaz; "
                          "kurumun bilgi işlem birimiyle DNS TXT kaydı ekleyerek doğrulayın.",
        }.get(st["reason"], "E-posta adresinizden geçerli bir alan adı çıkarılamadı."))
    if not st["verified"]:
        raise VerifyError("Önce e-posta adresinizi doğrulayın: kurumsal Google veya Microsoft hesabınızla giriş "
                          "yapın ya da e-postanıza gelen doğrulama kodunu girin.")
    domain = normalize_target(st["domain"])
    existing = {t["host"]: t for t in list_targets(user["id"])}
    with closing(get_db_connection()) as conn, conn:
        if domain in existing:
            conn.execute("UPDATE targets SET method = 'email', verified_at = ? WHERE id = ?",
                         (_now(), existing[domain]["id"]))
            target_id = existing[domain]["id"]
        else:
            plan = effective_plan(user)
            if plan.targets != UNLIMITED and len(existing) >= plan.targets:
                raise PlanError(f"{plan.name} planında en fazla {plan.targets} hedef eklenebilir. Planınızı yükseltin.")
            target_id = conn.execute(
                "INSERT INTO targets (user_id, host, token, method, verified_at, created_at) VALUES (?, ?, ?, 'email', ?, ?)",
                (user["id"], domain, f"email:{st['email']}", _now(), _now())).lastrowid
    return {"id": target_id, "host": domain, "method": "email"}


def _parents(host: str) -> list:
    """sub.firma.com -> [sub.firma.com, firma.com] (yalnızca TLD olan parçayı içermez)."""
    labels = host.split(".")
    return [".".join(labels[i:]) for i in range(len(labels) - 1)]


def _now():
    return datetime.now().replace(microsecond=0).isoformat(" ")


def list_targets(user_id):
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, host, token, method, verified_at, created_at FROM targets WHERE user_id = ? ORDER BY id",
            (user_id,)).fetchall()
    return [dict(r) for r in rows]


def add_target(user, raw_host: str) -> dict:
    host = normalize_target(raw_host)  # geçersizse ValueError
    plan = effective_plan(user)
    existing = list_targets(user["id"])
    if any(t["host"] == host for t in existing):
        raise VerifyError("Bu hedef zaten listenizde.")
    if plan.targets != UNLIMITED and len(existing) >= plan.targets:
        raise PlanError(f"{plan.name} planında en fazla {plan.targets} hedef eklenebilir. Planınızı yükseltin.")
    token = TOKEN_PREFIX + secrets.token_hex(16)
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute("INSERT INTO targets (user_id, host, token, created_at) VALUES (?, ?, ?, ?)",
                           (user["id"], host, token, _now()))
    return {"id": cur.lastrowid, "host": host, "token": token, "method": None, "verified_at": None}


def delete_target(user_id, target_id) -> bool:
    with closing(get_db_connection()) as conn, conn:
        return conn.execute("DELETE FROM targets WHERE id = ? AND user_id = ?", (target_id, user_id)).rowcount > 0


def _is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    return all(ipaddress.ip_address(info[4][0]).is_global for info in infos)


async def _check_dns(client: httpx.AsyncClient, host: str, token: str) -> bool:
    """TXT kaydı hedefin kendisinde ya da üst alan adında (www.firma.com için firma.com) olabilir:
    ana alan adının DNS'ini yöneten kişi alt alan adlarını da yönetir."""
    for name in _parents(host):
        try:
            res = await client.get(DOH_URL, params={"name": name, "type": "TXT"},
                                   headers={"Accept": "application/dns-json"})
            answers = res.json().get("Answer", [])
        except (httpx.HTTPError, ValueError):
            continue
        if any(token in a.get("data", "").replace('"', "") for a in answers):
            return True
    return False


async def _check_file(client: httpx.AsyncClient, host: str, token: str) -> bool:
    for scheme in ("https", "http"):
        try:
            res = await client.get(f"{scheme}://{host}{WELL_KNOWN}")
        except httpx.HTTPError:
            continue
        if res.status_code == 200 and token in res.text:
            return True
    return False


async def verify_target(user_id, target_id) -> dict:
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT * FROM targets WHERE id = ? AND user_id = ?", (target_id, user_id)).fetchone()
    if row is None:
        raise VerifyError("Hedef bulunamadı.")
    host, token = row["host"], row["token"]
    # Sunucunun kendi iç ağına istek atılmasını engelle (SSRF)
    if not config.ALLOW_PRIVATE_TARGETS and not _is_public_host(host):
        raise VerifyError("İç ağ adresleri bu sunucuda doğrulanamaz.")

    method = None
    async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
        if not _is_ip(host) and await _check_dns(client, host, token):
            method = "dns"
        elif await _check_file(client, host, token):
            method = "file"
    if method is None:
        raise VerifyError("Doğrulama anahtarı bulunamadı. DNS kaydının yayılması birkaç dakika sürebilir; "
                          "kaydı veya dosyayı kontrol edip tekrar deneyin.")
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE targets SET method = ?, verified_at = ? WHERE id = ?", (method, _now(), target_id))
    return {"id": target_id, "host": host, "method": method}


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def ensure_allowed(user_id, target: str):
    """REQUIRE_TARGET_VERIFICATION açıksa hedefin doğrulanmış olmasını şart koşar."""
    if not config.REQUIRE_TARGET_VERIFICATION:
        return
    host = normalize_target(target)
    if host in ALWAYS_ALLOWED:
        return
    with closing(get_db_connection()) as conn:
        rows = conn.execute("SELECT host, method FROM targets WHERE user_id = ? AND verified_at IS NOT NULL",
                            (user_id,)).fetchall()
    # Tam eşleşme her yöntemde geçerli. DNS veya kurumsal e-postayla doğrulanmış alan adı, alt alan adlarını
    # da kapsar (www.firma.com, mail.firma.com). Dosya yöntemi yalnızca o sunucuyu kanıtladığı için kapsamaz.
    ok = any(r["host"] == host or (r["method"] in ("dns", "email") and not _is_ip(host)
                                   and host.endswith("." + r["host"])) for r in rows)
    if not ok:
        raise VerifyError(f"{host} doğrulanmış hedefleriniz arasında değil. Bu sunucuda yalnızca sahipliği "
                          f"kanıtlanmış hedefler taranabilir (Abonelik → Doğrulanmış hedefler).")
