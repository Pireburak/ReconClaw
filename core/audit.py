"""
Denetim kaydı (audit log).

Giriş denemeleri, plan değişiklikleri, API anahtarı işlemleri ve yönetici eylemleri gibi
güvenlik açısından önemli olaylar burada kayıt altına alınır. Kullanıcı kendi hesabının
kaydını Ayarlar'da, yönetici tüm kayıtları Yönetim panelinde görür.
"""

from contextlib import closing
from datetime import datetime

from core.db_manager import get_db_connection

# eylem -> arayüzde gösterilen açıklama
ACTIONS = {
    "login": "Giriş yapıldı",
    "login_failed": "Hatalı giriş denemesi",
    "register": "Hesap oluşturuldu",
    "oauth_login": "Sosyal giriş",
    "password_change": "Parola değiştirildi",
    "token_create": "API anahtarı oluşturuldu",
    "token_revoke": "API anahtarı iptal edildi",
    "sessions_revoke": "Diğer oturumlar kapatıldı",
    "plan_checkout": "Plan değiştirildi",
    "plan_cancel": "Abonelik iptal edildi",
    "payment_paid": "Ödeme alındı",
    "payment_failed": "Ödeme başarısız",
    "payment_bad_hash": "Geçersiz ödeme bildirimi",
    "password_reset_request": "Şifre sıfırlama istendi",
    "password_reset": "Şifre e-postayla sıfırlandı",
    "monitor_create": "İzleme görevi eklendi",
    "monitor_delete": "İzleme görevi silindi",
    "share_create": "Rapor paylaşıma açıldı",
    "share_revoke": "Rapor paylaşımı kapatıldı",
    "admin_role": "Yönetici rolü değişti",
    "admin_plan": "Yönetici plan atadı",
    "admin_disable": "Hesap askıya alındı",
    "admin_enable": "Hesap yeniden açıldı",
    "admin_delete": "Hesap yönetici tarafından silindi",
}


def _now():
    return datetime.now().replace(microsecond=0).isoformat(" ")


def log(action: str, user_id=None, actor_id=None, detail: str = "", ip: str = ""):
    """Bir olayı kaydeder. Kayıt hatası asıl isteği asla bozmamalı."""
    try:
        with closing(get_db_connection()) as conn, conn:
            conn.execute(
                "INSERT INTO audit_log (user_id, actor_id, action, detail, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, actor_id if actor_id is not None else user_id, action, (detail or "")[:300],
                 (ip or "")[:64], _now()),
            )
    except Exception:  # noqa: BLE001
        pass


def entries(user_id=None, limit: int = 50, action: str = "") -> list:
    """user_id verilirse yalnızca o kullanıcının kayıtları, verilmezse tümü (yönetici)."""
    sql = ("SELECT a.id, a.user_id, a.actor_id, a.action, a.detail, a.ip, a.created_at, "
           "u.email AS user_email, act.email AS actor_email FROM audit_log a "
           "LEFT JOIN users u ON u.id = a.user_id LEFT JOIN users act ON act.id = a.actor_id WHERE 1 = 1")
    params = []
    if user_id is not None:
        sql += " AND a.user_id = ?"
        params.append(user_id)
    if action:
        sql += " AND a.action = ?"
        params.append(action)
    sql += " ORDER BY a.id DESC LIMIT ?"
    params.append(max(1, min(limit, 500)))
    with closing(get_db_connection()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [{**dict(r), "label": ACTIONS.get(r["action"], r["action"])} for r in rows]
