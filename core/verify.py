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
# Herkese açık, taranmasına izin verilmiş test sunucuları
ALWAYS_ALLOWED = {"scanme.nmap.org"}


class VerifyError(Exception):
    pass


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
    try:
        res = await client.get(DOH_URL, params={"name": host, "type": "TXT"},
                               headers={"Accept": "application/dns-json"})
        answers = res.json().get("Answer", [])
    except (httpx.HTTPError, ValueError):
        return False
    return any(token in a.get("data", "").replace('"', "") for a in answers)


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
        ok = conn.execute(
            "SELECT 1 FROM targets WHERE user_id = ? AND host = ? AND verified_at IS NOT NULL",
            (user_id, host)).fetchone()
    if not ok:
        raise VerifyError(f"{host} doğrulanmış hedefleriniz arasında değil. Bu sunucuda yalnızca sahipliği "
                          f"kanıtlanmış hedefler taranabilir (Abonelik → Doğrulanmış hedefler).")
