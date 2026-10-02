"""
ReconClaw v8.0 Cortex — tehdit istihbaratı katmanı.

Bir tarama raporunu üç farklı mercekten yorumlar (tamamı çevrimdışı, kural tabanlı ve
deterministiktir; aynı rapor her zaman aynı sonucu verir):

  1. MITRE ATT&CK eşlemesi: açık servisler ve bulgular, bir saldırganın kullanabileceği
     tekniklere (Enterprise matrisi) bağlanır ve taktik sırasına göre bir saldırı zinciri
     (kill chain) çıkarılır.
  2. Güvenlik karnesi: beş kategori (ağ maruziyeti, yama düzeyi, şifreleme, web
     sıkılaştırma, bilgi ifşası) 0–100 puanlanır ve A+…F harf notuna çevrilir. SSL Labs'te
     olduğu gibi kritik sorunlar notu tavanlar: bilinen CVE varken not en fazla D olabilir.
  3. Uyum ön değerlendirmesi: ISO/IEC 27001:2022 Ek A kontrolleri ve 6698 sayılı KVKK
     m.12 (veri güvenliği) için uyumlu / kısmi / uyumsuz sınıflandırması.

Not: Uyum çıktısı otomatik bir ön değerlendirmedir, resmi denetim yerine geçmez.
"""

import re

from core.engine import DATABASE_PORTS

ATTACK_URL = "https://attack.mitre.org/techniques/{}/"

# Enterprise ATT&CK taktikleri (matristeki sırayla)
TACTICS = [
    ("TA0043", "Reconnaissance", "Keşif"),
    ("TA0042", "Resource Development", "Kaynak Geliştirme"),
    ("TA0001", "Initial Access", "İlk Erişim"),
    ("TA0002", "Execution", "Çalıştırma"),
    ("TA0003", "Persistence", "Kalıcılık"),
    ("TA0004", "Privilege Escalation", "Yetki Yükseltme"),
    ("TA0005", "Defense Evasion", "Savunmadan Kaçınma"),
    ("TA0006", "Credential Access", "Kimlik Bilgisi Erişimi"),
    ("TA0007", "Discovery", "Ağ İçi Keşif"),
    ("TA0008", "Lateral Movement", "Yanal Hareket"),
    ("TA0009", "Collection", "Veri Toplama"),
    ("TA0011", "Command and Control", "Komuta Kontrol"),
    ("TA0010", "Exfiltration", "Veri Sızdırma"),
    ("TA0040", "Impact", "Etki"),
]
TACTIC_INDEX = {t[0]: i for i, t in enumerate(TACTICS)}

# teknik -> (İngilizce ad, Türkçe ad, taktikler)
TECHNIQUES = {
    "T1595": ("Active Scanning", "Aktif tarama", ["TA0043"]),
    "T1592.002": ("Gather Victim Host Information: Software", "Yazılım sürümü toplama", ["TA0043"]),
    "T1190": ("Exploit Public-Facing Application", "Dışa açık uygulamanın istismarı", ["TA0001"]),
    "T1133": ("External Remote Services", "Dış uzak erişim servisleri", ["TA0001", "TA0003"]),
    "T1078.001": ("Valid Accounts: Default Accounts", "Varsayılan hesaplar", ["TA0001", "TA0003", "TA0004", "TA0005"]),
    "T1059": ("Command and Scripting Interpreter", "Komut yorumlayıcısı ile çalıştırma", ["TA0002"]),
    "T1505.003": ("Server Software Component: Web Shell", "Web kabuğu", ["TA0003"]),
    "T1110": ("Brute Force", "Kaba kuvvet / parola deneme", ["TA0006"]),
    "T1040": ("Network Sniffing", "Ağ dinleme", ["TA0006", "TA0007"]),
    "T1557": ("Adversary-in-the-Middle", "Ortadaki saldırgan", ["TA0006", "TA0009"]),
    "T1135": ("Network Share Discovery", "Ağ paylaşımı keşfi", ["TA0007"]),
    "T1210": ("Exploitation of Remote Services", "Uzak servislerin istismarı", ["TA0008"]),
    "T1021.001": ("Remote Services: Remote Desktop Protocol", "Uzak masaüstü (RDP)", ["TA0008"]),
    "T1021.002": ("Remote Services: SMB/Windows Admin Shares", "SMB yönetim paylaşımları", ["TA0008"]),
    "T1021.004": ("Remote Services: SSH", "SSH ile uzak erişim", ["TA0008"]),
    "T1021.005": ("Remote Services: VNC", "VNC ile uzak erişim", ["TA0008"]),
    "T1048.003": ("Exfiltration Over Unencrypted Non-C2 Protocol", "Şifresiz protokolle veri sızdırma", ["TA0010"]),
    "T1485": ("Data Destruction", "Veri imhası", ["TA0040"]),
    "T1486": ("Data Encrypted for Impact", "Fidye amaçlı şifreleme", ["TA0040"]),
    "T1498.002": ("Network Denial of Service: Reflection Amplification", "Yansıtmalı DoS (amplifikasyon)", ["TA0040"]),
}

# port -> o servisin açık olmasıyla mümkün hale gelen teknikler
PORT_TECHNIQUES = {
    21: ["T1110", "T1040", "T1078.001", "T1048.003"],
    22: ["T1133", "T1110", "T1021.004"],
    23: ["T1133", "T1110", "T1040"],
    53: ["T1498.002"],
    80: ["T1040"],
    110: ["T1110", "T1040"],
    111: ["T1498.002"],
    135: ["T1210"],
    139: ["T1135"],
    143: ["T1110", "T1040"],
    445: ["T1135", "T1210", "T1021.002", "T1486"],
    1433: ["T1110", "T1078.001", "T1485"],
    1521: ["T1110", "T1485"],
    2049: ["T1135"],
    3306: ["T1110", "T1078.001", "T1485"],
    3389: ["T1133", "T1110", "T1021.001", "T1210", "T1486"],
    5432: ["T1110", "T1078.001", "T1485"],
    5900: ["T1133", "T1110", "T1021.005"],
    6379: ["T1078.001", "T1485"],
    8080: ["T1040"],
    9200: ["T1078.001", "T1485"],
    27017: ["T1078.001", "T1485"],
}
# Saldırı zincirinde öne çıkarılacak teknikler (yüksek = daha belirleyici adım)
CHAIN_WEIGHT = {"T1190": 5, "T1486": 5, "T1485": 4, "T1210": 4, "T1059": 4, "T1505.003": 3, "T1133": 3,
                "T1110": 3, "T1557": 3, "T1078.001": 2, "T1592.002": 2}
WEB_PORTS = {80, 443, 8000, 8008, 8080, 8443, 8888}
CLEARTEXT_AUTH = {21: "FTP", 23: "Telnet", 110: "POP3", 143: "IMAP"}
CRITICAL_EXPOSURE = DATABASE_PORTS | {23, 135, 139, 445, 2049, 3389, 5900}
REMOTE_ADMIN = {22, 3389, 5900}
VERSION_RE = re.compile(r"\d+\.\d+")


def _cve_ports(report) -> set:
    return {int(m.group(1)) for a in report.get("cve_alerts", []) if (m := re.search(r"Port (\d+)", a))}


def _findings(report, plugin=None, severities=None):
    return [f for f in report.get("findings", [])
            if (plugin is None or f["plugin"] == plugin) and (severities is None or f["severity"] in severities)]


# ---------------------------------------------------------------- 1. MITRE ATT&CK
def attack_mapping(report) -> dict:
    hits = {}  # teknik -> {"ports": set, "reasons": list}

    def add(tid, port, reason):
        item = hits.setdefault(tid, {"ports": set(), "reasons": []})
        if port is not None:
            item["ports"].add(port)
        if reason not in item["reasons"]:
            item["reasons"].append(reason)

    ports = report.get("analysis", [])
    if ports:
        add("T1595", None, f"{len(ports)} açık TCP servisi internetten taranarak bulunabiliyor.")
    for p in ports:
        port, service = p["port"], p.get("service", "?")
        for tid in PORT_TECHNIQUES.get(port, []):
            add(tid, port, f"{port}/{service} açık")
        if p.get("banner") and VERSION_RE.search(p["banner"]):
            add("T1592.002", port, f"{port}/{service} sürüm bilgisini ifşa ediyor: {p['banner'][:60]}")

    for port in _cve_ports(report):
        service = next((p.get("service", "?") for p in ports if p["port"] == port), "?")
        add("T1190", port, f"{port}/{service} üzerinde bilinen zafiyet imzası")
        add("T1059", port, f"{port}/{service} istismarı uzaktan komut çalıştırmaya yol açabilir")
        if port in WEB_PORTS:
            add("T1505.003", port, f"{port}/{service} web sunucusu ele geçirilirse kalıcı web kabuğu yerleştirilebilir")
        else:
            add("T1210", port, f"{port}/{service} zafiyeti iç ağda yanal hareket için kullanılabilir")

    for f in report.get("findings", []):
        if f["plugin"] == "tls_cert" and f["severity"] in ("high", "medium"):
            add("T1557", f["port"], f"TLS: {f['title']}")
        if "strict-transport-security" in f["title"].lower():
            add("T1557", f["port"], "HSTS yok: HTTPS'ten HTTP'ye düşürme (SSL stripping) mümkün")
    if any(p["port"] in WEB_PORTS and p["port"] != 443 for p in ports) and not any(p["port"] in (443, 8443) for p in ports):
        add("T1557", None, "Yalnızca şifresiz HTTP sunuluyor")

    tactics = []
    for tac_id, en, tr in TACTICS:
        techs = []
        for tid, item in hits.items():
            name, name_tr, tacs = TECHNIQUES[tid]
            if tac_id in tacs:
                techs.append({"id": tid, "name": name, "tr": name_tr, "url": ATTACK_URL.format(tid.replace(".", "/")),
                              "ports": sorted(item["ports"]), "reasons": item["reasons"]})
        techs.sort(key=lambda t: (-len(t["ports"]), t["id"]))
        tactics.append({"id": tac_id, "name": en, "tr": tr, "techniques": techs})

    # Saldırı zinciri: matris sırasıyla her taktikten bir teknik. Önce etkisi büyük teknikler
    # (CVE istismarı, fidye, veri imhası) seçilir ve bir teknik zincirde yalnızca bir kez yer alır.
    chain, used = [], set()
    for t in tactics:
        candidates = sorted((x for x in t["techniques"] if x["id"] not in used),
                            key=lambda x: (-CHAIN_WEIGHT.get(x["id"], 1), -len(x["ports"]), x["id"]))
        if candidates:
            pick = candidates[0]
            used.add(pick["id"])
            chain.append({"tactic": t["tr"], "tactic_id": t["id"], "technique": pick["id"], "name": pick["tr"]})
    return {
        "tactics": tactics,
        "techniques": len(hits),
        "tactics_covered": sum(1 for t in tactics if t["techniques"]),
        "chain": chain,
        "narrative": _narrative(chain),
    }


def tr_lower(text: str) -> str:
    """Türkçe küçük harf: str.lower() 'İ' harfini noktalı 'i̇' yapar, 'I' harfini 'i' yapar."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def _narrative(chain) -> str:
    if not chain:
        return "Dışarıdan erişilebilir bir servis bulunmadığı için belirgin bir saldırı yolu çıkarılamadı."
    steps = [f"{tr_lower(c['tactic'])} aşamasında {tr_lower(c['name'])} ({c['technique']})" for c in chain]
    return "Olası saldırı yolu: " + " → ".join(steps) + "."


# ---------------------------------------------------------------- 2. güvenlik karnesi
GRADES = [(95, "A+"), (85, "A"), (70, "B"), (55, "C"), (40, "D"), (0, "F")]
GRADE_ORDER = [g for _, g in GRADES]


def grade_of(score: int) -> str:
    return next(g for limit, g in GRADES if score >= limit)


def _cap(grade: str, ceiling: str) -> str:
    return grade if GRADE_ORDER.index(grade) >= GRADE_ORDER.index(ceiling) else ceiling


def scorecard(report) -> dict:
    ports = report.get("analysis", [])
    open_ports = {p["port"] for p in ports}
    cves = report.get("cve_alerts", [])
    cats = []

    # Ağ maruziyeti
    score, notes = 100, []
    for p in ports:
        if p["port"] in CRITICAL_EXPOSURE:
            score -= 25
            notes.append(f"{p['port']}/{p.get('service')} internete açık olmamalı")
        elif p["port"] in REMOTE_ADMIN:
            score -= 6
            notes.append(f"{p['port']}/{p.get('service')} yönetim servisi dışarıda (VPN arkasına alın)")
        elif p["port"] not in (80, 443):
            score -= 6
            notes.append(f"{p['port']}/{p.get('service')} gerekli mi?")
    cats.append(("exposure", "Ağ maruziyeti", 0.30, score, notes))

    # Yama düzeyi
    score = 100 - 45 * len(cves)
    cats.append(("patching", "Yama düzeyi", 0.30, score, [c.split("] ", 1)[-1] for c in cves]))

    # Şifreleme
    score, notes = 100, []
    for port, name in CLEARTEXT_AUTH.items():
        if port in open_ports:
            score -= 35 if port == 23 else 20
            notes.append(f"{name} ({port}) kimlik bilgilerini şifresiz taşır")
    if open_ports & {80, 8080} and not open_ports & {443, 8443}:
        score -= 20
        notes.append("HTTPS sunulmuyor")
    for f in _findings(report, "tls_cert", ("high", "medium")):
        score -= 30 if f["severity"] == "high" else 15
        notes.append(f"TLS: {f['title']}")
    for f in report.get("findings", []):
        if "strict-transport-security" in f["title"].lower():
            score -= 10
            notes.append("HSTS başlığı eksik")
            break
    cats.append(("encryption", "Şifreleme", 0.20, score, notes))

    # Web sıkılaştırma (yalnızca web servisi varsa)
    if open_ports & WEB_PORTS:
        weights = {"high": 25, "medium": 15, "low": 8, "info": 3}
        web = [f for f in _findings(report, "http_headers") if not f["title"].lower().startswith("sürüm")]
        score = 100 - sum(weights.get(f["severity"], 0) for f in web)
        cats.append(("web", "Web sıkılaştırma", 0.10, score, [f["title"] for f in web]))

    # Bilgi ifşası
    score, notes = 100, []
    for p in ports:
        if p.get("banner") and VERSION_RE.search(p["banner"]):
            score -= 10
            notes.append(f"{p['port']}: {p['banner'][:50]}")
    for f in report.get("findings", []):
        if f["title"].lower().startswith("sürüm ifşası"):
            score -= 10
            notes.append(f["title"])
    cats.append(("disclosure", "Bilgi ifşası", 0.10, score, notes))

    categories = [{"key": k, "name": n, "weight": w, "score": max(0, min(100, s)), "grade": grade_of(max(0, s)),
                   "notes": notes[:6]} for k, n, w, s, notes in cats]
    total_w = sum(c["weight"] for c in categories)
    overall = round(sum(c["score"] * c["weight"] for c in categories) / total_w)
    grade = grade_of(overall)
    caps = []
    if cves:
        grade = _cap(grade, "D")
        caps.append("Bilinen CVE imzası bulunduğu için not en fazla D olabilir.")
    elif open_ports & CRITICAL_EXPOSURE:
        grade = _cap(grade, "C")
        caps.append("Veritabanı / dosya paylaşımı / uzak masaüstü dışarıya açık olduğu için not en fazla C olabilir.")
    return {"score": overall, "grade": grade, "categories": categories, "caps": caps}


# ---------------------------------------------------------------- 3. uyum ön değerlendirmesi
def _join(items) -> str:
    return ", ".join(str(i) for i in items)


def compliance(report, monitored: bool = False) -> dict:
    ports = report.get("analysis", [])
    open_ports = {p["port"] for p in ports}
    cves = report.get("cve_alerts", [])
    exposed_db = sorted(open_ports & DATABASE_PORTS)
    exposed_crit = sorted(open_ports & CRITICAL_EXPOSURE)
    cleartext = sorted(open_ports & set(CLEARTEXT_AUTH))
    tls_bad = _findings(report, "tls_cert", ("high",))
    tls_mid = _findings(report, "tls_cert", ("medium",))
    hsts = any("strict-transport-security" in f["title"].lower() for f in report.get("findings", []))
    headers_mid = _findings(report, "http_headers", ("medium", "high"))
    headers_low = _findings(report, "http_headers", ("low",))
    disclosure = [p["port"] for p in ports if p.get("banner") and VERSION_RE.search(p["banner"])]
    remote = sorted(open_ports & REMOTE_ADMIN)
    http_only = bool(open_ports & {80, 8080}) and not open_ports & {443, 8443}

    def ctl(cid, name, status, evidence):
        return {"id": cid, "name": name, "status": status, "evidence": evidence}

    controls = [
        ctl("A.8.8", "Teknik açıklıkların yönetimi",
            "fail" if cves else "partial" if disclosure else "pass",
            cves[:3] or ([f"Sürüm ifşa eden portlar: {_join(disclosure)}"] if disclosure else ["Bilinen zafiyet imzası yok"])),
        ctl("A.8.9", "Yapılandırma yönetimi",
            "fail" if headers_mid or 23 in open_ports else "partial" if headers_low or disclosure else "pass",
            ([f["title"] for f in headers_mid + headers_low][:4] + (["Telnet etkin"] if 23 in open_ports else [])
             + ([f"Sürüm ifşa eden portlar: {_join(disclosure)}"] if disclosure else []))
            or ["Belirgin yapılandırma hatası yok"]),
        ctl("A.8.20", "Ağ güvenliği",
            "fail" if exposed_crit else "partial" if len(ports) > 5 else "pass",
            [f"Kritik servisler dışarıda: {_join(exposed_crit)}"] if exposed_crit else [f"{len(ports)} açık port"]),
        ctl("A.8.21", "Ağ hizmetlerinin güvenliği",
            "fail" if cleartext else "partial" if http_only else "pass",
            [f"Şifresiz kimlik doğrulama: {_join(CLEARTEXT_AUTH[p] for p in cleartext)}"] if cleartext
            else ["Yalnızca HTTP sunuluyor"] if http_only else ["Şifresiz yönetim servisi yok"]),
        ctl("A.8.22", "Ağların ayrımı",
            "fail" if exposed_db else "pass",
            [f"Veritabanı portları internetten erişilebilir: {_join(exposed_db)}"] if exposed_db
            else ["Veritabanı servisleri dışarıdan görünmüyor"]),
        ctl("A.8.24", "Kriptografi kullanımı",
            "fail" if tls_bad or {21, 23} & open_ports else "partial" if tls_mid or hsts or http_only else "pass",
            [f["title"] for f in tls_bad + tls_mid][:3] + (["HSTS eksik"] if hsts else [])
            or (["Şifresiz protokol açık"] if {21, 23} & open_ports else ["Şifreleme sorunu tespit edilmedi"])),
        ctl("A.8.5", "Güvenli kimlik doğrulama",
            "fail" if {21, 23, 5900} & open_ports else "partial" if remote else "pass",
            [f"Dışarıdan oturum açılabilen servisler: {_join(sorted(open_ports & ({21, 23} | REMOTE_ADMIN)))}"]
            if open_ports & ({21, 23} | REMOTE_ADMIN) else ["Dışarıya açık oturum servisi yok"]),
        ctl("A.8.16", "İzleme faaliyetleri",
            "pass" if monitored else "partial",
            ["ReconClaw sürekli izleme görevi tanımlı"] if monitored else ["Bu hedef için sürekli izleme tanımlı değil"]),
        ctl("KVKK m.12", "Veri güvenliğine ilişkin yükümlülükler (6698 sayılı Kanun)",
            "fail" if exposed_db or cves else "partial" if cleartext or http_only else "pass",
            (["Kişisel veri içerebilecek veritabanı dışarıya açık"] if exposed_db else [])
            + (["Uzaktan istismar edilebilir zafiyet var"] if cves else [])
            or (["Şifresiz veri aktarımı"] if cleartext or http_only else ["Belirgin teknik tedbir eksikliği yok"])),
    ]
    summary = {s: sum(1 for c in controls if c["status"] == s) for s in ("pass", "partial", "fail")}
    return {
        "framework": "ISO/IEC 27001:2022 Ek A + KVKK",
        "controls": controls,
        "summary": summary,
        "score": round((summary["pass"] + summary["partial"] * 0.5) / len(controls) * 100),
        "disclaimer": "Otomatik ön değerlendirmedir; dışarıdan görülebilen bulgulara dayanır ve resmi denetim yerine geçmez.",
    }


def analyze(report, monitored: bool = False) -> dict:
    return {"scorecard": scorecard(report), "attack": attack_mapping(report), "compliance": compliance(report, monitored)}
