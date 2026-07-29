import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="data/reconclaw_v4.db"):
        # Data klasörü yoksa oluştur
        os.makedirs("data", exist_ok=True)
        
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        """Veritabanı tablolarını sıfırdan kurar"""
        # Hedefler Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                scan_date TEXT,
                status TEXT
            )
        ''')
        
        # Subdomain / Zafiyet Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                type TEXT,
                value TEXT,
                severity TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id)
            )
        ''')
        self.conn.commit()

    def add_finding(self, domain, finding_type, value, severity="INFO"):
        """Yeni bir bulgu (subdomain, açık vs.) ekler"""
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Önce hedefi ekle veya bul
        self.cursor.execute('INSERT OR IGNORE INTO targets (domain, scan_date, status) VALUES (?, ?, ?)', 
                            (domain, date, 'scanned'))
        self.cursor.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
        target_id = self.cursor.fetchone()[0]

        # Bulguyu ekle
        self.cursor.execute('INSERT INTO findings (target_id, type, value, severity) VALUES (?, ?, ?, ?)',
                            (target_id, finding_type, value, severity))
        self.conn.commit()
        return True

    def close(self):
        self.conn.close()

# Test için (Sadece bu dosyayı çalıştırdığında çalışır)
if __name__ == "__main__":
    db = DatabaseManager()
    db.add_finding("example.com", "SUBDOMAIN", "api.example.com", "INFO")
    db.add_finding("example.com", "VULNERABILITY", "SQL Injection on /login", "CRITICAL")
    print("[+] Veritabanı başarıyla kuruldu ve test verisi eklendi!")
