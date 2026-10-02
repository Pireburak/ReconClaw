"""
Yönetim paneli işlemleri: sistem özeti, kullanıcı listesi, rol / plan / askıya alma.

Yalnızca role = 'admin' olan kullanıcılar erişebilir (kontrol main.py'deki admin_user bağımlılığında).
Yöneticinin kendini askıya alması, rolünü düşürmesi veya silmesi engellenir; böylece sistem
yöneticisiz kalmaz.
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
            "admins": sum(1 for u in users if u["role"] == "admin"),
            "disabled": sum(1 for u in users if u["disabled"]),
            "scans_total": q("SELECT COUNT(*) FROM scans"),
            "scans_today": q("SELECT COALESCE(SUM(scans), 0) FROM usage WHERE day = ?", today),
            "ai_today": q("SELECT COALESCE(SUM(ai), 0) FROM usage WHERE day = ?", today),
            "sessions_active": q("SELECT COUNT(*) FROM sessions WHERE expires_at > ?", now),
            "monitors_active": q("SELECT COUNT(*) FROM monitors WHERE enabled = 1"),
            "alerts_7d": q("SELECT COUNT(*) FROM alerts WHERE created_at >= ?", _days(7)[0]),
            "revenue_total": q("SELECT COALESCE(SUM(COALESCE(amount_try, amount)), 0) FROM payments"),
            "payments_total": q("SELECT COUNT(*) FROM payments"),
            "failed_logins_24h": q("SELECT COUNT(*) FROM audit_log WHERE action = 'login_failed' AND created_at >= ?",
                                   (datetime.now() - timedelta(days=1)).replace(microsecond=0).isoformat(" ")),
        }

    by_plan = {pid: 0 for pid in plans.PLANS}
    mrr = 0
    for u in users:
        if u["role"] == "admin":
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
            "(SELECT COALESCE(SUM(COALESCE(amount_try, amount)), 0) FROM payments p WHERE p.user_id = u.id) AS paid "
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


def update_user(actor, user_id: int, role=None, plan=None, days=None, disabled=None, ip="") -> dict:
    target = auth.get_user(user_id)
    if target is None:
        raise AdminError("Kullanıcı bulunamadı.")
    is_self = target["id"] == actor["id"]
    events = []  # denetim kayıtları işlem bittikten sonra yazılır (SQLite tek yazar kilidi)
    with closing(get_db_connection()) as conn, conn:
        if role is not None and role != target["role"]:
            if role not in ("user", "admin"):
                raise AdminError("Geçersiz rol.")
            if is_self:
                raise AdminError("Kendi yönetici rolünüzü kaldıramazsınız.")
            conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            events.append(("admin_role", f"{target['role']} → {role}"))
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
    audit.log("admin_delete", None, actor["id"], target["email"], ip)
    auth.delete_user(user_id)
