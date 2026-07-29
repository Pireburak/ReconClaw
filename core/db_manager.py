import sqlite3
import os

# Veritabanı dosyasının yolu (main.py'nin olduğu ana dizinde olacak)
DB_PATH = "reconclaw_v4.db"

def get_db_connection():
    """Veritabanına bağlanır ve bağlantı nesnesini döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Verileri sözlük (dictionary) formatında almamızı sağlar
    return conn

def init_db():
    """Veritabanı tablolarını ilk kez oluşturmak için kullanılır."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Örnek bir tablo: Taramalar (Scans)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_ip TEXT NOT NULL,
            status TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Veritabanı ve tablolar hazır!")

# Dosya doğrudan çalıştırılırsa tabloları oluştur
if __name__ == "__main__":
    init_db()
