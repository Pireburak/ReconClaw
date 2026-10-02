"""
Pasif keşif (OSINT): hedefe tek bir paket göndermeden saldırı yüzeyini çıkarır.

  * Alt alan adları: Sertifika Şeffaflığı (Certificate Transparency) kayıtları — crt.sh,
    yanıt vermezse CertSpotter. Bir alan adı için verilmiş her TLS sertifikası herkese açık
    loglara yazıldığından, unutulmuş test / yönetim sunucuları da burada görünür.
  * DNS kayıtları: A, AAAA, MX, NS, TXT, CAA (DNS-over-HTTPS ile)
  * E-posta güvenliği: SPF, DMARC ve CAA politikalarının değerlendirilmesi
  * Dikkat çeken alt alan adları: admin, dev, test, vpn, jenkins... gibi adlar işaretlenir

MITRE ATT&CK karşılığı: T1596.003 (Digital Certificates), T1590.002 (DNS).
"""

import asyncio
import json
import re
import socket
import time
from contextlib import closing
from datetime import datetime

import httpx

from core.db_manager import get_db_connection
from core.engine import normalize_target

DOH_URL = "https://cloudflare-dns.com/dns-query"
CRTSH_URL = "https://crt.sh/"
CERTSPOTTER_URL = "https://api.certspotter.com/v1/issuances"
RECORD_TYPES = ("A", "AAAA", "MX", "NS", "TXT", "CAA")
MAX_SUBDOMAINS = 300
USER_AGENT = "ReconClaw-Recon/8.0 (+https://github.com/Pireburak/ReconClaw)"

# Saldırganın ilk bakacağı türden adlar: etiket -> anahtar kelimeler
INTERESTING = {
    "yönetim": ("admin", "panel", "manage", "cpanel", "plesk", "webmin", "dashboard", "portal"),
    "geliştirme": ("dev", "test", "staging", "stage", "uat", "qa", "beta", "demo", "sandbox", "preprod"),
    "uzak erişim": ("vpn", "rdp", "remote", "citrix", "ssh", "gateway", "owa", "exchange"),
    "ci/cd": ("jenkins", "gitlab", "git", "ci", "build", "jira", "confluence", "sonar", "registry"),
    "veri": ("db", "sql", "mysql", "mongo", "redis", "elastic", "kibana", "grafana", "backup", "ftp", "files"),
    "api": ("api", "graphql", "ws", "internal", "intranet"),
}


class ReconError(Exception):
    pass


def normalize_domain(raw: str) -> str:
    host = normalize_target(raw)
    if re.fullmatch(r"[\d.]+|.*:.*", host) or "." not in host:
        raise ReconError("Pasif keşif için bir alan adı girin (ör. ornek.com); IP adresi kabul edilmez.")
    return host


def tags_for(name: str, domain: str) -> list:
    labels = re.split(r"[.\-_]", name[: -len(domain)].rstrip(".")) if name != domain else []
    found = []
    for tag, words in INTERESTING.items():
        if any(label in words or any(label.startswith(w) and len(w) >= 3 for w in words) for label in labels if label):
            found.append(tag)
    return found


def _clean_names(names, domain: str) -> list:
    out = set()
    for raw in names:
        for name in str(raw).lower().split("\n"):
            name = name.strip().lstrip("*.").rstrip(".")
            if name == domain or name.endswith("." + domain):
                if re.fullmatch(r"[a-z0-9.\-_]+", name):
                    out.add(name)
    return sorted(out, key=lambda n: (n.count("."), n))[:MAX_SUBDOMAINS]


async def _crtsh(client: httpx.AsyncClient, domain: str) -> list:
    res = await client.get(CRTSH_URL, params={"q": f"%.{domain}", "output": "json"}, timeout=25)
    res.raise_for_status()
    return [row.get("name_value", "") for row in res.json()]


async def _certspotter(client: httpx.AsyncClient, domain: str) -> list:
    res = await client.get(CERTSPOTTER_URL, params={"domain": domain, "include_subdomains": "true",
                                                    "expand": "dns_names"}, timeout=20)
    res.raise_for_status()
    return [n for row in res.json() for n in row.get("dns_names", [])]


async def certificate_names(client: httpx.AsyncClient, domain: str) -> tuple[list, str]:
    """CT loglarından alt alan adlarını toplar; (adlar, kaynak) döndürür."""
    for source, fn in (("crt.sh", _crtsh), ("CertSpotter", _certspotter)):
        try:
            names = _clean_names(await fn(client, domain), domain)
            return names, source
        except (httpx.HTTPError, ValueError, TypeError):
            continue
    return [], "erişilemedi"


async def dns_query(client: httpx.AsyncClient, name: str, rtype: str) -> list:
    try:
        res = await client.get(DOH_URL, params={"name": name, "type": rtype},
                               headers={"Accept": "application/dns-json"}, timeout=8)
        answers = res.json().get("Answer", [])
    except (httpx.HTTPError, ValueError):
        return []
    want = {"A": 1, "NS": 2, "MX": 15, "TXT": 16, "AAAA": 28, "CAA": 257}[rtype]
    return [a.get("data", "").strip() for a in answers if a.get("type") == want]


async def dns_records(client: httpx.AsyncClient, domain: str) -> dict:
    results = await asyncio.gather(*(dns_query(client, domain, t) for t in RECORD_TYPES))
    records = dict(zip(RECORD_TYPES, results))
    records["TXT"] = [t.replace('" "', "").strip('"') for t in records["TXT"]]
    records["DMARC"] = [t.replace('" "', "").strip('"') for t in await dns_query(client, f"_dmarc.{domain}", "TXT")]
    return records


def email_security(records: dict) -> dict:
    """SPF / DMARC / CAA kayıtlarını değerlendirir ve bulgu listesi üretir."""
    findings = []
    spf = [t for t in records.get("TXT", []) if t.lower().startswith("v=spf1")]
    dmarc = [t for t in records.get("DMARC", []) if t.lower().startswith("v=dmarc1")]
    caa = records.get("CAA", [])
    has_mail = bool(records.get("MX"))

    spf_state = "yok"
    if len(spf) > 1:
        spf_state = "hatalı"
        findings.append({"severity": "high", "title": "Birden fazla SPF kaydı",
                         "detail": "RFC 7208'e göre tek SPF kaydı olmalı; birden fazlası SPF'i geçersiz kılar (permerror)."})
    elif spf:
        policy = spf[0].split()[-1].lower()
        spf_state = {"-all": "katı", "~all": "esnek", "?all": "nötr", "+all": "tehlikeli"}.get(policy, "eksik")
        if policy == "+all":
            findings.append({"severity": "high", "title": "SPF herkese izin veriyor (+all)",
                             "detail": "Herhangi bir sunucu bu alan adı adına e-posta gönderebilir. -all kullanın."})
        elif policy in ("?all", "~all"):
            findings.append({"severity": "low", "title": f"SPF politikası esnek ({policy})",
                             "detail": "Sahte e-postalar reddedilmez, yalnızca işaretlenir. Hazır olduğunuzda -all'a geçin."})
        elif policy != "-all":
            findings.append({"severity": "medium", "title": "SPF kaydı 'all' ile bitmiyor",
                             "detail": "Kayıt sonuna -all veya ~all ekleyin."})
    elif has_mail:
        findings.append({"severity": "high", "title": "SPF kaydı yok",
                         "detail": "Alan adınız adına sahte e-posta (spoofing) gönderilebilir. TXT 'v=spf1 ... -all' ekleyin."})

    dmarc_state = "yok"
    if dmarc:
        m = re.search(r"\bp=(\w+)", dmarc[0], re.I)
        dmarc_state = (m.group(1).lower() if m else "eksik")
        if dmarc_state == "none":
            findings.append({"severity": "medium", "title": "DMARC yalnızca izliyor (p=none)",
                             "detail": "Sahte e-postalar teslim edilmeye devam eder. p=quarantine veya p=reject kullanın."})
        elif dmarc_state not in ("quarantine", "reject"):
            findings.append({"severity": "medium", "title": "DMARC politikası geçersiz", "detail": dmarc[0][:120]})
    elif has_mail or spf:
        findings.append({"severity": "medium", "title": "DMARC kaydı yok",
                         "detail": "_dmarc alt alan adına 'v=DMARC1; p=quarantine; rua=mailto:...' TXT kaydı ekleyin."})

    if not caa:
        findings.append({"severity": "low", "title": "CAA kaydı yok",
                         "detail": "Hangi sertifika otoritelerinin sertifika verebileceğini CAA kaydıyla sınırlayın."})

    weights = {"high": 30, "medium": 15, "low": 5}
    score = max(0, 100 - sum(weights.get(f["severity"], 0) for f in findings))
    return {"spf": spf_state, "spf_record": spf[0] if spf else None, "dmarc": dmarc_state,
            "dmarc_record": dmarc[0] if dmarc else None, "caa": bool(caa), "mail": has_mail,
            "score": score, "findings": findings}


async def _resolve(name: str, sem: asyncio.Semaphore) -> list:
    async with sem:
        try:
            infos = await asyncio.wait_for(
                asyncio.get_running_loop().getaddrinfo(name, None, family=socket.AF_INET, type=socket.SOCK_STREAM),
                timeout=4)
        except (socket.gaierror, asyncio.TimeoutError, OSError, UnicodeError):
            return []
    return sorted({info[4][0] for info in infos})


async def run(raw_domain: str) -> dict:
    domain = normalize_domain(raw_domain)
    started = time.perf_counter()
    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        (names, source), records = await asyncio.gather(certificate_names(client, domain), dns_records(client, domain))
    if domain not in names:
        names = [domain, *names]
    sem = asyncio.Semaphore(25)
    ips = await asyncio.gather(*(_resolve(n, sem) for n in names))
    subdomains = [{"name": n, "ips": ip, "alive": bool(ip), "tags": tags_for(n, domain)} for n, ip in zip(names, ips)]
    email = email_security(records)
    return {
        "domain": domain,
        "source": source,
        "duration": round(time.perf_counter() - started, 2),
        "summary": {
            "subdomains": len(subdomains),
            "alive": sum(1 for s in subdomains if s["alive"]),
            "interesting": sum(1 for s in subdomains if s["tags"]),
            "unique_ips": len({ip for s in subdomains for ip in s["ips"]}),
        },
        "subdomains": subdomains,
        "dns": records,
        "email": email,
    }


# ---------------------------------------------------------------- kayıtlar
def save_run(user_id, result: dict) -> int:
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute("INSERT INTO recon_runs (user_id, domain, result, created_at) VALUES (?, ?, ?, ?)",
                           (user_id, result["domain"], json.dumps(result, ensure_ascii=False),
                            datetime.now().replace(microsecond=0).isoformat(" ")))
        # Kullanıcı başına son 30 keşif saklanır
        conn.execute("DELETE FROM recon_runs WHERE user_id = ? AND id NOT IN "
                     "(SELECT id FROM recon_runs WHERE user_id = ? ORDER BY id DESC LIMIT 30)", (user_id, user_id))
    return cur.lastrowid


def list_runs(user_id) -> list:
    with closing(get_db_connection()) as conn:
        rows = conn.execute("SELECT id, domain, result, created_at FROM recon_runs WHERE user_id = ? ORDER BY id DESC",
                            (user_id,)).fetchall()
    out = []
    for r in rows:
        data = json.loads(r["result"])
        out.append({"id": r["id"], "domain": r["domain"], "created_at": r["created_at"],
                    "summary": data["summary"], "email_score": data["email"]["score"]})
    return out


def get_run(user_id, run_id) -> dict | None:
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT * FROM recon_runs WHERE id = ? AND user_id = ?", (run_id, user_id)).fetchone()
    if row is None:
        return None
    return {**json.loads(row["result"]), "id": row["id"], "created_at": row["created_at"]}
