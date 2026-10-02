"""
Sürekli izleme (Continuous Attack Surface Monitoring).

Kullanıcı bir hedef için saatlik / günlük / haftalık izleme görevi tanımlar. Arka plandaki
zamanlayıcı zamanı gelen görevleri tarar, sonucu bir önceki taramayla karşılaştırır ve
değişiklikleri alarm olarak kaydeder:

  * yeni açılan port (veritabanı / uzak erişim portuysa kritik)
  * yeni CVE imzası, yeni yüksek/orta şiddetli eklenti bulgusu
  * servis sürümünün değişmesi, risk skorunun 10 puan veya daha fazla artması
  * kapanan port ve giderilen zafiyet (bilgi amaçlı)

İsteğe bağlı webhook adresine (Discord, Slack veya kendi sunucunuz) JSON bildirim gönderilir.
"""

import asyncio
import logging
from contextlib import closing
from datetime import datetime, timedelta
from urllib.parse import urlparse

import httpx

from core import audit, auth, config, plans
from core.db_manager import get_db_connection, get_scan_report
from core.engine import DATABASE_PORTS, normalize_target
from core.insights import compare_reports

log = logging.getLogger("reconclaw.monitor")

INTERVALS = {"hourly": 3600, "daily": 86400, "weekly": 7 * 86400}
INTERVAL_LABELS = {"hourly": "Saatlik", "daily": "Günlük", "weekly": "Haftalık"}
CRITICAL_EXPOSURE = DATABASE_PORTS | {23, 135, 139, 445, 3389, 5900}
LEVEL_ORDER = ["critical", "high", "medium", "low", "info"]


class MonitorError(Exception):
    pass


def _now():
    return datetime.now().replace(microsecond=0)


def _iso(dt):
    return dt.isoformat(" ")


# ---------------------------------------------------------------- görev yönetimi
def list_monitors(user_id) -> list:
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT m.*, (SELECT COUNT(*) FROM alerts a WHERE a.monitor_id = m.id) AS alert_count, "
            "s.risk_score AS last_risk, s.open_count AS last_open FROM monitors m "
            "LEFT JOIN scans s ON s.id = m.last_scan_id WHERE m.user_id = ? ORDER BY m.id", (user_id,)).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["enabled"] = bool(item["enabled"])
        item["interval_label"] = INTERVAL_LABELS.get(item["interval"], item["interval"])
        item["webhook"] = _mask(item["webhook"])
        result.append(item)
    return result


def _mask(url):
    # Webhook adresleri gizli anahtar içerir; arayüzde yalnızca alan adı gösterilir
    if not url:
        return None
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.hostname}/…"


def validate_webhook(url: str | None) -> str | None:
    url = (url or "").strip()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or len(url) > 500:
        raise MonitorError("Webhook adresi http(s):// ile başlayan geçerli bir adres olmalı.")
    if not config.ALLOW_PRIVATE_TARGETS:
        from core.verify import _is_public_host
        if not _is_public_host(parsed.hostname):
            raise MonitorError("Webhook adresi iç ağa yönlendirilemez.")
    return url


def create_monitor(user, target: str, interval: str, max_port: int | None = None, webhook: str | None = None) -> dict:
    plan = plans.require(user, "monitoring", "Sürekli izleme Pro ve üzeri planlarda kullanılabilir.")
    if interval not in INTERVALS:
        raise MonitorError("Geçersiz izleme aralığı.")
    if interval == "hourly" and not plan.hourly:
        raise plans.PlanError("Saatlik izleme Ultra ve üzeri planlarda kullanılabilir.")
    if max_port and max_port > plan.max_port:
        raise plans.PlanError(f"{plan.name} planında en fazla 1–{plan.max_port} port aralığı izlenebilir.")
    host = normalize_target(target)  # geçersizse ValueError
    webhook = validate_webhook(webhook)
    existing = list_monitors(user["id"])
    if plan.monitors != plans.UNLIMITED and len(existing) >= plan.monitors:
        raise plans.PlanError(f"{plan.name} planında en fazla {plan.monitors} izleme görevi tanımlanabilir.")
    if any(m["target"] == host and m["interval"] == interval for m in existing):
        raise MonitorError("Bu hedef için aynı aralıkta bir izleme görevi zaten var.")
    now = _now()
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO monitors (user_id, target, interval, max_port, webhook, next_run, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], host, interval, max_port, webhook, _iso(now), _iso(now)))
    audit.log("monitor_create", user["id"], detail=f"{host} · {INTERVAL_LABELS[interval]}")
    return next(m for m in list_monitors(user["id"]) if m["id"] == cur.lastrowid)


def is_monitored(user_id, target: str) -> bool:
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT 1 FROM monitors WHERE user_id = ? AND target = ? AND enabled = 1",
                            (user_id, target)).fetchone() is not None


def get_monitor(user_id, monitor_id):
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT * FROM monitors WHERE id = ? AND user_id = ?", (monitor_id, user_id)).fetchone()


def set_enabled(user_id, monitor_id, enabled: bool) -> bool:
    with closing(get_db_connection()) as conn, conn:
        return conn.execute("UPDATE monitors SET enabled = ?, next_run = CASE WHEN ? THEN ? ELSE next_run END "
                            "WHERE id = ? AND user_id = ?",
                            (int(enabled), int(enabled), _iso(_now()), monitor_id, user_id)).rowcount > 0


def delete_monitor(user_id, monitor_id) -> bool:
    row = get_monitor(user_id, monitor_id)
    if row is None:
        return False
    with closing(get_db_connection()) as conn, conn:
        conn.execute("DELETE FROM monitors WHERE id = ?", (monitor_id,))
    audit.log("monitor_delete", user_id, detail=row["target"])
    return True


# ---------------------------------------------------------------- alarmlar
def list_alerts(user_id, limit: int = 50, unseen: bool = False) -> list:
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE user_id = ? AND (? = 0 OR seen = 0) ORDER BY id DESC LIMIT ?",
            (user_id, int(unseen), max(1, min(limit, 200)))).fetchall()
    return [dict(r) for r in rows]


def unseen_count(user_id) -> int:
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT COUNT(*) FROM alerts WHERE user_id = ? AND seen = 0", (user_id,)).fetchone()[0]


def mark_seen(user_id) -> int:
    with closing(get_db_connection()) as conn, conn:
        return conn.execute("UPDATE alerts SET seen = 1 WHERE user_id = ? AND seen = 0", (user_id,)).rowcount


def change_alerts(old: dict | None, new: dict) -> list:
    """İki tarama arasındaki güvenlik açısından önemli değişiklikleri alarm listesine çevirir."""
    if old is None:
        return [{"level": "info", "title": "İzleme başladı",
                 "detail": f"Başlangıç durumu: {new['total_open']} açık port, risk %{new['overall_risk']}."}]
    d = compare_reports(old, new)
    out = []
    for p in d["opened"]:
        level = "critical" if p["port"] in CRITICAL_EXPOSURE else "high"
        out.append({"level": level, "title": f"Yeni açık port: {p['port']}/{p['service']}",
                    "detail": p.get("banner") or "Önceki taramada kapalıydı."})
    for c in d["new_cves"]:
        out.append({"level": "critical", "title": "Yeni zafiyet imzası", "detail": c})
    for f in d["new_findings"]:
        if f["severity"] in ("high", "medium"):
            out.append({"level": f["severity"], "title": f"Yeni bulgu: {f['title']}", "detail": f"Port {f['port']} · {f['plugin']}"})
    for c in d["changed"]:
        out.append({"level": "medium", "title": f"Servis sürümü değişti: {c['port']}/{c['service']}",
                    "detail": f"{c['old_banner'] or '—'} → {c['new_banner'] or '—'}"})
    if d["risk_delta"] >= 10:
        out.append({"level": "high", "title": f"Risk skoru arttı: {d['old']['overall_risk']} → {d['new']['overall_risk']}",
                    "detail": f"+{d['risk_delta']} puan"})
    for p in d["closed"]:
        out.append({"level": "info", "title": f"Port kapandı: {p['port']}/{p['service']}", "detail": ""})
    for c in d["resolved_cves"]:
        out.append({"level": "info", "title": "Zafiyet giderildi", "detail": c})
    if d["risk_delta"] <= -10:
        out.append({"level": "info", "title": f"Risk skoru düştü: {d['old']['overall_risk']} → {d['new']['overall_risk']}",
                    "detail": f"{d['risk_delta']} puan"})
    return sorted(out, key=lambda a: LEVEL_ORDER.index(a["level"]))


def _save_alerts(user_id, monitor_id, scan_id, target, items):
    now = _iso(_now())
    with closing(get_db_connection()) as conn, conn:
        conn.executemany(
            "INSERT INTO alerts (user_id, monitor_id, scan_id, target, level, title, detail, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(user_id, monitor_id, scan_id, target, a["level"], a["title"][:200], (a["detail"] or "")[:500], now)
             for a in items])


async def send_webhook(url: str, target: str, items: list, scan_id=None):
    lines = [f"[{a['level'].upper()}] {a['title']}" + (f" — {a['detail']}" if a["detail"] else "") for a in items[:15]]
    text = f"🦝 ReconClaw izleme · {target}\n" + "\n".join(lines)
    payload = {
        "text": text,          # Slack
        "content": text[:1900],  # Discord
        "reconclaw": {"target": target, "scan_id": scan_id, "alerts": items},
    }
    try:
        validate_webhook(url)
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(url, json=payload)
    except (httpx.HTTPError, MonitorError) as exc:
        log.warning("webhook gönderilemedi: %s", exc)


# ---------------------------------------------------------------- çalıştırma
async def run_monitor(row, scan_fn) -> dict:
    """Tek bir izleme görevini çalıştırır; üretilen alarmları döndürür."""
    user = auth.get_user(row["user_id"])
    now = _now()
    next_run = _iso(now + timedelta(seconds=INTERVALS.get(row["interval"], 86400)))
    if user is None or user["disabled"]:
        return {"status": "skipped", "alerts": []}
    plan = plans.effective_plan(user)
    if not plan.monitoring or (row["interval"] == "hourly" and not plan.hourly):
        status = "Plan bu izlemeyi içermiyor; görev duraklatıldı."
        with closing(get_db_connection()) as conn, conn:
            conn.execute("UPDATE monitors SET enabled = 0, last_status = ? WHERE id = ?", (status, row["id"]))
        items = [{"level": "medium", "title": "İzleme duraklatıldı", "detail": status}]
        _save_alerts(user["id"], row["id"], None, row["target"], items)
        return {"status": status, "alerts": items}

    try:
        report = await scan_fn(user, row["target"], row["max_port"], 1.0, True)
    except Exception as exc:  # noqa: BLE001 — kota, DNS, doğrulama vb. hatalar alarm olarak raporlanır
        status = str(getattr(exc, "detail", exc))[:200]
        items = [{"level": "medium", "title": "İzleme taraması yapılamadı", "detail": status}]
        _save_alerts(user["id"], row["id"], None, row["target"], items)
        with closing(get_db_connection()) as conn, conn:
            conn.execute("UPDATE monitors SET last_run = ?, next_run = ?, last_status = ? WHERE id = ?",
                         (_iso(now), next_run, f"HATA: {status}", row["id"]))
        return {"status": "error", "alerts": items}

    previous = get_scan_report(row["last_scan_id"], user["id"]) if row["last_scan_id"] else None
    items = change_alerts(previous, report)
    if previous is not None and not items:
        status = "Değişiklik yok"
    else:
        status = f"{len([a for a in items if a['level'] != 'info'])} önemli değişiklik" if previous else "Başlangıç taraması"
    if items:
        _save_alerts(user["id"], row["id"], report["scan_id"], row["target"], items)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE monitors SET last_run = ?, next_run = ?, last_scan_id = ?, last_status = ? WHERE id = ?",
                     (_iso(now), next_run, report["scan_id"], status, row["id"]))
    important = [a for a in items if a["level"] != "info"]
    if row["webhook"] and important:
        await send_webhook(row["webhook"], row["target"], important, report["scan_id"])
    return {"status": status, "alerts": items, "scan_id": report["scan_id"]}


def due_monitors(limit: int = 5) -> list:
    with closing(get_db_connection()) as conn:
        return conn.execute(
            "SELECT * FROM monitors WHERE enabled = 1 AND next_run <= ? ORDER BY next_run LIMIT ?",
            (_iso(_now()), limit)).fetchall()


async def scheduler_loop(scan_fn, tick: float = 30):
    """Zamanı gelen izleme görevlerini sırayla çalıştırır (aynı anda en fazla 5 görev / tur)."""
    while True:
        try:
            for row in due_monitors():
                await run_monitor(row, scan_fn)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — zamanlayıcı tek bir hatayla durmamalı
            log.exception("izleme turu başarısız")
        await asyncio.sleep(tick)
