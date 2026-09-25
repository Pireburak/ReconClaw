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
        ''')
        # v4.0 ilk sürümünde tam rapor sütunu yoktu
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(scans)")}
        if "report" not in columns:
            conn.execute("ALTER TABLE scans ADD COLUMN report TEXT")


def save_scan(report):
    """Tamamlanan bir tarama raporunu (API yanıtı) kaydeder, kayıt id'sini döndürür."""
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO scans (target, ip_address, open_count, risk_score, risk_level, duration, scan_time, report) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (report["target"], report["resolved_ip"], report["total_open"], report["overall_risk"],
             report["risk_level"]["label"], report["duration"], report["scan_time"],
             json.dumps(report, ensure_ascii=False)),
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


def get_recent_scans(limit=20):
    """Son taramaları en yeniden eskiye doğru döndürür."""
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, target, ip_address, open_count, risk_score, risk_level, duration, scan_time, "
            "report IS NOT NULL AS has_report FROM scans ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_scan_report(scan_id):
    """Kayıtlı bir taramanın tam raporunu döndürür; yoksa None."""
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT report FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if row is None or row["report"] is None:
        return None
    report = json.loads(row["report"])
    report["scan_id"] = scan_id
    return report


# Dosya doğrudan çalıştırılırsa tabloları oluştur
if __name__ == "__main__":
    init_db()
    print(f"Veritabanı hazır: {DB_PATH}")
