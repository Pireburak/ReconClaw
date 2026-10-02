import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime

# Veritabanı dosyası proje kökündeki data/ klasöründe tutulur
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("RECONCLAW_DB", os.path.join(BASE_DIR, "data", "reconclaw_v4.db"))


def get_db_connection():
    """Veritabanına bağlanır ve bağlantı nesnesini döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Satırlara sütun adıyla erişebilmek için
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Veritabanı tablolarını (yoksa) oluşturur."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with closing(get_db_connection()) as conn, conn:
        # Eski sürümün 'scans' tablosu farklı şemadaydı; verisini kaybetmeden kenara al
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(scans)")}
        if columns and "ip_address" not in columns:
            conn.execute("ALTER TABLE scans RENAME TO scans_legacy")

        conn.executescript('''
            CREATE TABLE IF NOT EXISTS scans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target      TEXT NOT NULL,
                ip_address  TEXT NOT NULL,
                open_count  INTEGER NOT NULL,
                risk_score  INTEGER NOT NULL,
                risk_level  TEXT NOT NULL,
                duration    REAL,
                scan_time   TEXT NOT NULL,
                report      TEXT
            );
            CREATE TABLE IF NOT EXISTS open_ports (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id  INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                port     INTEGER NOT NULL,
                protocol TEXT,
                service  TEXT,
                banner   TEXT,
                risk     INTEGER
            );
            CREATE TABLE IF NOT EXISTS findings (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id  INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                plugin   TEXT NOT NULL,
                port     INTEGER,
                severity TEXT NOT NULL,
                title    TEXT NOT NULL,
                detail   TEXT
            );
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name          TEXT NOT NULL,
                password_hash TEXT,
                avatar_url    TEXT,
                api_token     TEXT UNIQUE,
                created_at    TEXT NOT NULL,
                last_login    TEXT
            );
            CREATE TABLE IF NOT EXISTS identities (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                subject  TEXT NOT NULL,
                UNIQUE (provider, subject)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                user_agent TEXT
            );
            CREATE TABLE IF NOT EXISTS usage (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                day     TEXT NOT NULL,
                scans   INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, day)
            );
            CREATE TABLE IF NOT EXISTS payments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                plan       TEXT NOT NULL,
                period     TEXT NOT NULL,
                amount     INTEGER NOT NULL,
                currency   TEXT NOT NULL,
                status     TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS targets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                host        TEXT NOT NULL,
                token       TEXT NOT NULL,
                method      TEXT,
                verified_at TEXT,
                created_at  TEXT NOT NULL,
                UNIQUE (user_id, host)
            );
            CREATE TABLE IF NOT EXISTS oauth_states (
                state      TEXT PRIMARY KEY,
                provider   TEXT NOT NULL,
                verifier   TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                actor_id   INTEGER,
                action     TEXT NOT NULL,
                detail     TEXT,
                ip         TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, id);
            CREATE TABLE IF NOT EXISTS monitors (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target        TEXT NOT NULL,
                interval      TEXT NOT NULL,
                max_port      INTEGER,
                webhook       TEXT,
                enabled       INTEGER NOT NULL DEFAULT 1,
                last_run      TEXT,
                next_run      TEXT NOT NULL,
                last_scan_id  INTEGER,
                last_status   TEXT,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                monitor_id INTEGER REFERENCES monitors(id) ON DELETE SET NULL,
                scan_id    INTEGER,
                target     TEXT NOT NULL,
                level      TEXT NOT NULL,
                title      TEXT NOT NULL,
                detail     TEXT,
                seen       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id, id);
            CREATE TABLE IF NOT EXISTS recon_runs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                domain     TEXT NOT NULL,
                result     TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id    INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                user_id    INTEGER NOT NULL,
                question   TEXT,
                answer     TEXT NOT NULL,
                engine     TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        ''')
        # v4.0 ilk sürümünde tam rapor sütunu, v5.0 öncesinde kullanıcı sütunu yoktu
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(scans)")}
        if "report" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN report TEXT")
        if "user_id" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER")
        # v6.1: abonelik planı
        user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        if "plan" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free'")
        if "plan_expires" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN plan_expires TEXT")
        # v7.0: yönetici rolü ve hesap askıya alma
        if "role" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        if "disabled" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN disabled INTEGER NOT NULL DEFAULT 0")
        # v8.0: günlük AI kullanımı ve paylaşılabilir rapor bağlantısı
        usage_columns = {row["name"] for row in conn.execute("PRAGMA table_info(usage)")}
        if "ai" not in usage_columns:
            conn.execute("ALTER TABLE usage ADD COLUMN ai INTEGER NOT NULL DEFAULT 0")
        # v8.1: bölgesel fiyatlandırma, ödemenin TL karşılığı ve ülkesi
        payment_columns = {row["name"] for row in conn.execute("PRAGMA table_info(payments)")}
        if "amount_try" not in payment_columns:
            conn.execute("ALTER TABLE payments ADD COLUMN amount_try INTEGER")
        if "country" not in payment_columns:
            conn.execute("ALTER TABLE payments ADD COLUMN country TEXT")
        if "share_token" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN share_token TEXT")


def save_scan(report, user_id=None):
    """Tamamlanan bir tarama raporunu (API yanıtı) kaydeder, kayıt id'sini döndürür."""
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO scans (target, ip_address, open_count, risk_score, risk_level, duration, scan_time, report, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (report["target"], report["resolved_ip"], report["total_open"], report["overall_risk"],
             report["risk_level"]["label"], report["duration"], report["scan_time"],
             json.dumps(report, ensure_ascii=False), user_id),
        )
        scan_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO open_ports (scan_id, port, protocol, service, banner, risk) VALUES (?, ?, ?, ?, ?, ?)",
            [(scan_id, p["port"], p["protocol"], p["service"], p["banner"], p["risk"]) for p in report["analysis"]],
        )
        conn.executemany(
            "INSERT INTO findings (scan_id, plugin, port, severity, title, detail) VALUES (?, ?, ?, ?, ?, ?)",
            [(scan_id, f["plugin"], f["port"], f["severity"], f["title"], f["detail"]) for f in report["findings"]],
        )
        return scan_id


def get_recent_scans(limit=20, user_id=None, query=""):
    """Kullanıcının son taramalarını en yeniden eskiye doğru döndürür."""
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, target, ip_address, open_count, risk_score, risk_level, duration, scan_time, "
            "report IS NOT NULL AS has_report FROM scans WHERE user_id IS ? "
            "AND (target LIKE ? OR ip_address LIKE ?) ORDER BY id DESC LIMIT ?",
            (user_id, f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_scan_report(scan_id, user_id=None):
    """Kullanıcıya ait kayıtlı bir taramanın tam raporunu döndürür; yoksa None."""
    with closing(get_db_connection()) as conn:
        row = conn.execute(
            "SELECT report FROM scans WHERE id = ? AND user_id IS ?", (scan_id, user_id)
        ).fetchone()
    if row is None or row["report"] is None:
        return None
    report = json.loads(row["report"])
    report["scan_id"] = scan_id
    return report


def get_user_reports(user_id, limit=200):
    """İstatistikler için kullanıcının son tam raporlarını (eskiden yeniye) döndürür."""
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, report FROM scans WHERE user_id IS ? AND report IS NOT NULL ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    reports = []
    for row in reversed(rows):
        report = json.loads(row["report"])
        report["scan_id"] = row["id"]
        reports.append(report)
    return reports


def delete_scans(user_id, scan_id=None):
    """Kullanıcının bir taramasını (scan_id verilirse) ya da tüm geçmişini siler; silinen sayısını döndürür."""
    with closing(get_db_connection()) as conn, conn:
        if scan_id is None:
            cur = conn.execute("DELETE FROM scans WHERE user_id IS ?", (user_id,))
        else:
            cur = conn.execute("DELETE FROM scans WHERE id = ? AND user_id IS ?", (scan_id, user_id))
        return cur.rowcount


def set_share_token(scan_id, user_id, token):
    """Rapor için paylaşım anahtarını ayarlar (None = paylaşımı kapat); kayıt yoksa False."""
    with closing(get_db_connection()) as conn, conn:
        return conn.execute("UPDATE scans SET share_token = ? WHERE id = ? AND user_id IS ?",
                            (token, scan_id, user_id)).rowcount > 0


def get_share_token(scan_id, user_id):
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT share_token FROM scans WHERE id = ? AND user_id IS ?", (scan_id, user_id)).fetchone()
    return row["share_token"] if row else None


def get_shared_report(token):
    """Paylaşım anahtarıyla raporu ve sahibinin id'sini döndürür; yoksa (None, None)."""
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT id, user_id, report FROM scans WHERE share_token = ?", (token,)).fetchone()
    if row is None or row["report"] is None:
        return None, None
    report = json.loads(row["report"])
    report["scan_id"] = row["id"]
    return report, row["user_id"]


def db_ok():
    try:
        with closing(get_db_connection()) as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False


# Dosya doğrudan çalıştırılırsa tabloları oluştur
if __name__ == "__main__":
    init_db()
    print(f"Veritabanı hazır: {DB_PATH}")
