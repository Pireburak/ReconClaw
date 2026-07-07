import asyncio
import socket
import sqlite3
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# ---------------------------------------------------------
# 1. VERİTABANI (SQLite) KURULUMU
# ---------------------------------------------------------
def init_db():
    """Uygulama başladığında veritabanını ve tabloları otomatik oluşturur"""
    conn = sqlite3.connect("reconclaw.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            ip_address TEXT,
            open_ports_count INTEGER,
            risk_score INTEGER,
            risk_level TEXT,
            scan_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 2. CORE ENGINE (Asenkron Tarayıcı & Banner Grabbing)
# ---------------------------------------------------------
class AsyncScanner:
    def __init__(self, target: str, timeout: float = 1.0):
        self.target = target
        self.timeout = timeout
        try:
            self.ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.ip = None

    async def scan_port(self, port: int):
        """Asenkron port tarama ve Versiyon okuma (v4.0)"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, port),
                timeout=self.timeout
            )
            banner = "Unknown Service"
            try:
                if port in [80, 443, 8080]:
                    writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
                else:
                    writer.write(b"\r\n")
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
                if data:
                    banner = data.decode('utf-8', errors='ignore').strip().split('\n')[0][:80]
            except Exception:
                pass
            finally:
                writer.close()
                await writer.wait_closed()
                
            return {"port": port, "protocol": "TCP", "state": "open", "banner": banner}
        except Exception:
            return None

    async def run_scan(self, ports: list):
        if not self.ip:
            return []
        
        tasks = [self.scan_port(port) for port in ports]
        results = await asyncio.gather(*tasks)
        return [res for res in results if res is not None]

# ---------------------------------------------------------
# 3. AI BRAIN (Risk Analizi ve Zafiyet Motoru)
# ---------------------------------------------------------
class AIBrain:
    CRITICAL_PORTS = {
        21: {"service": "FTP", "risk": 15},
        22: {"service": "SSH", "risk": 10},
        23: {"service": "Telnet", "risk": 25}, 
        80: {"service": "HTTP", "risk": 5},
        443: {"service": "HTTPS", "risk": 2},
        3306: {"service": "MySQL", "risk": 20}, 
        3389: {"service": "RDP", "risk": 20}
    }

    @classmethod
    def analyze(cls, open_ports: list):
        score = 0
        recommendations = []
        cve_alerts = []

        for item in open_ports:
            port = item['port']
            banner = item.get('banner', '').lower()
            
            if port in cls.CRITICAL_PORTS:
                score += cls.CRITICAL_PORTS[port]['risk']
                item['service'] = cls.CRITICAL_PORTS[port]['service']
            else:
                score += 2
                item['service'] = "Unknown"

            if "openssh" in banner and any(v in banner for v in [" 4.", " 5.", " 6."]):
                score += 30
                cve_alerts.append(f"Port {port}: Eski SSH Sürümü tespit edildi! (CVE-2016-10009).")
            if "apache/2.4.49" in banner:
                score += 50
                cve_alerts.append(f"Port {port}: Kritik Apache Path Traversal zafiyeti! (CVE-2021-41773).")
            if port in [3306, 5432, 1433]:
                recommendations.append(f"Kritik: Veritabanı portu ({port}) dış ağa açık. İç ağa kapatın.")

        score = min(100, score)

        if score == 0 and not open_ports: level = "🟢 Güvenli"
        elif score <= 25: level = "🟢 Düşük Risk"
        elif score <= 50: level = "🟡 Orta Risk"
        elif score <= 75: level = "🟠 Yüksek Risk"
        else: level = "🔴 Kritik Risk"

        if len(open_ports) > 0 and not recommendations:
            recommendations.append("Gereksiz portları güvenlik duvarından engelleyin ve servisleri güncel tutun.")

        return {
            "total_score": score,
            "risk_level": level,
            "cve_alerts": cve_alerts,
            "recommendations": list(set(recommendations)),
            "processed_ports": open_ports
        }

# ---------------------------------------------------------
# 4. FASTAPI (Web API & Endpoint'ler)
# ---------------------------------------------------------
app = FastAPI(title="ReconClaw v4.0 Ultimate", version="4.0")

class ScanRequest(BaseModel):
    target: str
    ports: List[int] = [21, 22, 23, 80, 443, 3306, 3389, 8080]

@app.post("/api/v4/scan")
async def start_scan(req: ScanRequest):
    scanner = AsyncScanner(target=req.target, timeout=1.5)
    
    if not scanner.ip:
        raise HTTPException(status_code=400, detail="Hedef adres çözümlenemedi. Geçerli bir URL veya IP girin.")

    raw_results = await scanner.run_scan(req.ports)
    analysis = AIBrain.analyze(raw_results)

    conn = sqlite3.connect("reconclaw.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scan_history (target, ip_address, open_ports_count, risk_score, risk_level, scan_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (req.target, scanner.ip, len(raw_results), analysis['total_score'], analysis['risk_level'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "target": req.target,
        "resolved_ip": scanner.ip,
        "open_ports_count": len(raw_results),
        "risk_report": analysis
    }

@app.get("/")
def home():
    return {"message": "🦅 ReconClaw v4.0 Aktif! Tarama paneli için tarayıcınızdan /docs adresine gidin."}

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" 🦅 ReconClaw v4.0 Ultimate Başlatılıyor...")
    print("="*50)
    print(" 👉 Test Paneli (Swagger UI): http://127.0.0.1:8000/docs ")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
