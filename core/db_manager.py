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
            CREATE TABLE IF NOT EXISTS oauth_states (
                state      TEXT PRIMARY KEY,
                provider   TEXT NOT NULL,
                verifier   TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        ''')
        # v4.0 ilk sürümünde tam rapor sütunu, v5.0 öncesinde kullanıcı sütunu yoktu
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(scans)")}
        if "report" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN report TEXT")
        if "user_id" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER")


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
