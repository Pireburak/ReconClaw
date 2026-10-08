"""
Yönetim paneli işlemleri: sistem özeti, kullanıcı listesi, rol / plan / askıya alma.

Yalnızca role = 'moderator', 'admin' veya 'owner' olan kullanıcılar erişebilir (kontrol main.py'deki
staff_user bağımlılığında). Yetki kuralları:
  * Sahip (owner) tektir; panelden değiştirilemez, askıya alınamaz, silinemez.
  * Yöneticiler üyeleri moderatör / yönetici yapabilir, plan atayabilir, üyeleri ve moderatörleri
    askıya alabilir / silebilir.
  * Bir yöneticinin yetkisini almak, onu askıya almak veya silmek yalnızca sahibin işidir.
  * Moderatörler paneli görür; yalnızca normal üyeleri askıya alıp yeniden açabilir. Rol, plan ve silme yetkisi yoktur.
  * Kimse kendi hesabını panelden askıya alamaz, yetkisini düşüremez veya silemez.
"""

from contextlib import closing
from datetime import date, datetime, timedelta

from core import audit, auth, plans
from core.db_manager import get_db_connection


class AdminError(Exception):
    pass


def _days(n: int) -> list:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


def overview() -> dict:
    now = datetime.now().replace(microsecond=0).isoformat(" ")
    today = date.today().isoformat()
    with closing(get_db_connection()) as conn:
        q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
        users = conn.execute("SELECT plan, plan_expires, role, disabled FROM users").fetchall()
        signups = dict(conn.execute(
            "SELECT substr(created_at, 1, 10) d, COUNT(*) FROM users WHERE created_at >= ? GROUP BY d",
            (_days(14)[0],)).fetchall())
        scans = dict(conn.execute(
            "SELECT substr(scan_time, 1, 10) d, COUNT(*) FROM scans WHERE scan_time >= ? GROUP BY d",
            (_days(14)[0],)).fetchall())
        data = {
            "users_total": len(users),
            "admins": sum(1 for u in users if u["role"] in plans.ADMIN_ROLES),
            "moderators": sum(1 for u in users if u["role"] == "moderator"),
            "disabled": sum(1 for u in users if u["disabled"]),
            "scans_total": q("SELECT COUNT(*) FROM scans"),
            "scans_today": q("SELECT COALESCE(SUM(scans), 0) FROM usage WHERE day = ?", today),
            "ai_today": q("SELECT COALESCE(SUM(ai), 0) FROM usage WHERE day = ?", today),
            "sessions_active": q("SELECT COUNT(*) FROM sessions WHERE expires_at > ?", now),
            "monitors_active": q("SELECT COUNT(*) FROM monitors WHERE enabled = 1"),
            "alerts_7d": q("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", _days(7)[0]),
            "revenue_total": q("SELECT COALESCE(SUM(COALESCE(amount_try, amount)), 0) FROM payments WHERE status IN ('paid', 'demo')"),
            "payments_total": q("SELECT COUNT(*) FROM payments WHERE status IN ('paid', 'demo')"),
            "failed_logins_24h": q("SELECT COUNT(*) FROM audit_log WHERE action = 'login_failed' AND created_at >= ?",
                                   (datetime.now() - timedelta(days=1)).replace(microsecond=0).isoformat(" ")),
        }

    by_plan = {pid: 0 for pid in plans.PLANS}
    mrr = 0
    for u in users:
        if u["role"] in plans.ADMIN_ROLES:
            continue
        plan = plans.PLANS.get(u["plan"] or "free", plans.PLANS["free"])
        if plan.id != "free" and u["plan_expires"] and u["plan_expires"] < now:
            plan = plans.PLANS["free"]
        by_plan[plan.id] += 1
        mrr += plan.price_monthly
    data["by_plan"] = [{"id": pid, "name": plans.PLANS[pid].name, "count": n} for pid, n in by_plan.items()]
    data["mrr"] = mrr  # aylık yinelenen gelir (aktif ücretli planların aylık fiyat toplamı)
    data["series"] = [{"date": d, "signups": signups.get(d, 0), "scans": scans.get(d, 0)} for d in _days(14)]
    return data


def list_users(query: str = "", limit: int = 100) -> list:
    like = f"%{query.strip()}%"
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT u.*, (SELECT COUNT(*) FROM scans s WHERE s.user_id = u.id) AS scan_count, "
            "(SELECT COALESCE(SUM(COALESCE(amount_try, amount)), 0) FROM payments p WHERE p.user_id = u.id AND p.status IN ('paid', 'demo')) AS paid "
            "FROM users u WHERE u.email LIKE ? OR u.name LIKE ? ORDER BY u.id DESC LIMIT ?",
            (like, like, max(1, min(limit, 500)))).fetchall()
    result = []
    for r in rows:
        plan = plans.effective_plan(r)
        result.append({
            "id": r["id"], "email": r["email"], "name": r["name"], "role": r["role"],
            "disabled": bool(r["disabled"]), "plan": plan.id, "plan_name": plan.name, "level": plan.level,
            "stored_plan": r["plan"], "plan_expires": r["plan_expires"], "created_at": r["created_at"],
            "last_login": r["last_login"], "scan_count": r["scan_count"], "paid": r["paid"],
            "scans_today": plans.usage_today(r["id"]),
        })
    return result


def _guard(actor, target, touches_admin: bool):
    """Sahip korunur; yöneticilere karşı işlem yalnızca sahibe açıktır."""
    if target["role"] == "owner" and target["id"] != actor["id"]:
        raise AdminError("Sahip hesabı değiştirilemez.")
    if touches_admin and target["role"] == "admin" and not plans.is_owner(actor):
        raise AdminError("Bir yöneticinin yetkisini almak, askıya almak veya silmek yalnızca sahibe açıktır.")


def _moderator_guard(actor, target, role, plan, days, disabled):
    """Moderatör yalnızca normal üyeleri askıya alıp yeniden açabilir."""
    if plans.is_admin(actor):
        return
    if role is not None or plan is not None or days is not None:
        raise AdminError("Moderatörler rol veya plan değiştiremez.")
    if disabled is not None and target["role"] != "user":
        raise AdminError("Moderatörler yalnızca normal üyeleri askıya alabilir.")


ROLE_NAMES = {"user": "üye", "moderator": "moderatör", "admin": "yönetici", "owner": "sahip"}


def update_user(actor, user_id: int, role=None, plan=None, days=None, disabled=None, ip="") -> dict:
    target = auth.get_user(user_id)
    if target is None:
        raise AdminError("Kullanıcı bulunamadı.")
    is_self = target["id"] == actor["id"]
    _moderator_guard(actor, target, role, plan, days, disabled)
    _guard(actor, target, touches_admin=(role is not None and role != target["role"]) or disabled is not None)
    events = []  # denetim kayıtları işlem bittikten sonra yazılır (SQLite tek yazar kilidi)
    with closing(get_db_connection()) as conn, conn:
        if role is not None and role != target["role"]:
            if role not in ("user", "moderator", "admin"):
                raise AdminError("Geçersiz rol. Sahiplik yalnızca terminalden (manage.py make-owner) devredilir.")
            if is_self:
                raise AdminError("Kendi rolünüzü değiştiremezsiniz.")
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            events.append(("admin_role", f"{ROLE_NAMES[target['role']]} → {ROLE_NAMES[role]}"))
        if disabled is not None and bool(disabled) != bool(target["disabled"]):
            if is_self:
                raise AdminError("Kendi hesabınızı askıya alamazsınız.")
            conn.execute("UPDATE users SET disabled = ? WHERE id = ?", (int(bool(disabled)), user_id))
            if disabled:
                # Askıya alınan kullanıcının tüm oturumları ve API anahtarı geçersiz olur
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                conn.execute("UPDATE users SET api_token = NULL WHERE id = ?", (user_id,))
            events.append(("admin_disable" if disabled else "admin_enable", ""))
    for action, detail in events:
        audit.log(action, user_id, actor["id"], detail, ip)
    if plan is not None:
        try:
            result = plans.grant(user_id, plan, days)
        except ValueError as exc:
            raise AdminError(str(exc)) from exc
        audit.log("admin_plan", user_id, actor["id"],
                  f"{plan} · {result['expires'][:10] if result['expires'] else 'süresiz'}", ip)
    return next(u for u in list_users(target["email"], 50) if u["id"] == user_id)


def delete_user(actor, user_id: int, ip=""):
    target = auth.get_user(user_id)
    if target is None:
        raise AdminError("Kullanıcı bulunamadı.")
    if target["id"] == actor["id"]:
        raise AdminError("Kendi hesabınızı yönetim panelinden silemezsiniz.")
    if not plans.is_admin(actor):
        raise AdminError("Moderatörler hesap silemez.")
    _guard(actor, target, touches_admin=True)
    audit.log("admin_delete", None, actor["id"], target["email"], ip)
    auth.delete_user(user_id)


def team() -> list:
    """Yetkili ekip: sahip, yöneticiler ve moderatörler; her biri için yetkiyi kimin ne zaman verdiği."""
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, email, name, role, last_login, created_at, disabled FROM users "
            "WHERE role IN ('owner', 'admin', 'moderator') "
            "ORDER BY CASE role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END, id").fetchall()
        result = []
        for r in rows:
            granted = conn.execute(
                "SELECT a.created_at, u.email AS actor_email FROM audit_log a LEFT JOIN users u ON u.id = a.actor_id "
                "WHERE a.action = 'admin_role' AND a.user_id = ? ORDER BY a.id DESC LIMIT 1", (r["id"],)).fetchone()
            result.append({
                "id": r["id"], "email": r["email"], "name": r["name"], "role": r["role"],
                "disabled": bool(r["disabled"]), "last_login": r["last_login"], "created_at": r["created_at"],
                "granted_at": granted["created_at"] if granted else None,
                "granted_by": granted["actor_email"] if granted else None,
            })
    return result


def list_payments(limit: int = 200, status: str = "") -> list:
    """Tüm kullanıcıların ödeme kayıtları (yalnızca sahip ve yöneticiler görür)."""
    sql = ("SELECT p.id, p.user_id, u.email, u.name, p.plan, p.period, p.amount, p.currency, p.amount_try, p.country, "
           "p.status, p.created_at, p.paid_at, p.merchant_oid, p.note FROM payments p "
           "LEFT JOIN users u ON u.id = p.user_id")
    args = []
    if status:
        sql += " WHERE p.status = ?"
        args.append(status)
    sql += " ORDER BY p.id DESC LIMIT ?"
    args.append(max(1, min(limit, 1000)))
    with closing(get_db_connection()) as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def clear_demo_payments() -> int:
    """Demo (kartsız deneme) ödeme kayıtlarını siler. Gerçek PayTR kayıtlarına dokunmaz."""
    with closing(get_db_connection()) as conn, conn:
        return conn.execute("DELETE FROM payments WHERE status = 'demo'").rowcount
