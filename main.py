import asyncio
import socket
import sqlite3
import json
import urllib.request
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# ==============================================================================
# 🎨 BÖLÜM 1: TERMİNAL RENKLERİ (CLI GÖRSELLİĞİ İÇİN)
# ==============================================================================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==============================================================================
# 🗄️ BÖLÜM 2: SQLITE VERİTABANI MOTORU
# ==============================================================================
DB_NAME = "reconclaw.db"

def init_db():
    """Uygulama ilk kez başlatıldığında veritabanını ve tabloları otomatik kurar."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                country TEXT,
                isp TEXT,
                open_ports_count INTEGER,
                risk_score INTEGER,
                risk_level TEXT,
                scan_time TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                port INTEGER,
                protocol TEXT,
                service TEXT,
                banner TEXT,
                FOREIGN KEY(scan_id) REFERENCES scan_history(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

# ==============================================================================
# ⚡ BÖLÜM 3: CORE SCANNER ENGINE (Asenkron TCP, UDP, OSINT & Banner Grabbing)
# ==============================================================================
class AsyncScanner:
    def __init__(self, target: str, timeout: float = 1.2):
        self.target = target
        self.timeout = timeout
        try:
            self.ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.ip = None

    def get_osint_data(self):
        """v4.0 OSINT: Hedefin coğrafi ve ASN (Servis Sağlayıcı) bilgilerini çeker"""
        if not self.ip:
            return {"country": "Bilinmiyor", "isp": "Bilinmiyor", "city": "Bilinmiyor"}
        try:
            url = f"http://ip-api.com/json/{self.ip}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "Bilinmiyor"),
                        "city": data.get("city", "Bilinmiyor"),
                        "isp": data.get("isp", "Bilinmiyor")
                    }
        except Exception:
            pass
        return {"country": "Bilinmiyor", "isp": "Bilinmiyor", "city": "Bilinmiyor"}

    async def scan_tcp_port(self, port: int):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, port),
                timeout=self.timeout
            )
            banner = "Unknown Service / No Banner"
            
            try:
                # Banner Grabbing: Servisi konuşturmak için istek gönder
                if port in [80, 443, 8080, 8443]:
                    writer.write(b"HEAD / HTTP/1.1\r\nHost: " + self.ip.encode() + b"\r\n\r\n")
                elif port in [21, 22, 25]:
                    await asyncio.sleep(0.2)
                else:
                    writer.write(b"\r\n")
                
                await writer.drain()
                
                data = await asyncio.wait_for(reader.read(1024), timeout=0.8)
                if data:
                    decoded_data = data.decode('utf-8', errors='ignore').strip()
                    if "HTTP" in decoded_data.upper():
                        for line in decoded_data.split('\n'):
                            if line.lower().startswith('server:'):
                                banner = line.strip()
                                break
                        if banner == "Unknown Service / No Banner":
                            banner = decoded_data.split('\n')[0][:80]
                    else:
                        banner = decoded_data.split('\n')[0][:80]
            except Exception:
                pass 
            finally:
                writer.close()
                await writer.wait_closed()
                
            return {"port": port, "protocol": "TCP", "state": "open", "banner": banner}
        except Exception:
            return None 

    async def scan_udp_port(self, port: int):
        """v4.0 UDP Taraması (Beta)"""
        if port not in [53, 123, 161]:
            return None
            
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            payload = b""
            if port == 53: # DNS
                payload = b"\xaa\xaa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01"
            elif port == 123: # NTP
                payload = b"\x1b" + 47 * b"\0"
            elif port == 161: # SNMP
                payload = b"\x30\x26\x02\x01\x00\x04\x06\x70\x75\x62\x6c\x69\x63\xa0\x19\x02\x04\x13\x25\x36\x47\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x05\x00"
            
            sock.sendto(payload, (self.ip, port))
            
            loop = asyncio.get_running_loop()
            data, _ = await loop.run_in_executor(None, sock.recvfrom, 1024)
            sock.close()
            
            service = "DNS" if port == 53 else "NTP" if port == 123 else "SNMP"
            return {"port": port, "protocol": "UDP", "state": "open", "banner": f"{service} Yanıtı Alındı"}
        except Exception:
            return None

    async def run_scan(self, tcp_ports: list, udp_ports: list = []):
        if not self.ip:
            return []
        
        # Concurrency: Bütün portları aynı anda asenkron tara
        tcp_tasks = [self.scan_tcp_port(port) for port in tcp_ports]
        udp_tasks = [self.scan_udp_port(port) for port in udp_ports]
        
        all_tasks = tcp_tasks + udp_tasks
        results = await asyncio.gather(*all_tasks)
        
        return [res for res in results if res is not None]

# ==============================================================================
# 🧠 BÖLÜM 4: AI BRAIN (Risk Analizi ve CVE Zafiyet Motoru)
# ==============================================================================
class AIBrain:
    CRITICAL_PORTS = {
        21: {"service": "FTP", "risk": 15},
        22: {"service": "SSH", "risk": 10},
        23: {"service": "Telnet", "risk": 25},
        25: {"service": "SMTP", "risk": 10},
        53: {"service": "DNS", "risk": 5},
        80: {"service": "HTTP", "risk": 5},
        110: {"service": "POP3", "risk": 10},
        123: {"service": "NTP", "risk": 5},
        161: {"service": "SNMP", "risk": 15},
        443: {"service": "HTTPS", "risk": 2},
        3306: {"service": "MySQL", "risk": 25},
        3389: {"service": "RDP", "risk": 20},
        5432: {"service": "PostgreSQL", "risk": 25},
        8080: {"service": "HTTP-Proxy", "risk": 10}
    }

    @classmethod
    def analyze(cls, open_ports: list):
        score = 0
        recommendations = []
        cve_alerts = []

        for item in open_ports:
            port = item['port']
            protocol = item.get('protocol', 'TCP')
            banner = item.get('banner', '').lower()
            
            if port in cls.CRITICAL_PORTS:
                score += cls.CRITICAL_PORTS[port]['risk']
                item['service'] = cls.CRITICAL_PORTS[port]['service']
            else:
                score += 2
                item['service'] = "Bilinmiyor"

            # v4.0 AI - Zafiyet (CVE) Simülasyonu
            if "openssh" in banner:
                if any(v in banner for v in [" 4.", " 5.", " 6."]):
                    score += 30
                    cve_alerts.append(f"Port {port}: Eski SSH Sürümü tespit edildi (CVE-2016-10009 RCE riski).")
            
            if "apache/2.4.49" in banner or "apache/2.4.50" in banner:
                score += 50
                cve_alerts.append(f"Port {port}: Kritik Apache Path Traversal Zafiyeti tespit edildi (CVE-2021-41773). Acil Yama!")

            if "iis/6.0" in banner:
                score += 40
                cve_alerts.append(f"Port {port}: Çok eski IIS sürümü tespit edildi! (CVE-2017-7269).")

            if port in [3306, 5432, 1433]:
                recommendations.append(f"Kritik: Veritabanı portu ({port}) dış ağa açık bırakılmış. Sadece iç ağa (LAN) izole edin.")
            
            if port == 23:
                recommendations.append(f"Kritik: Telnet (Port 23) şifresiz iletişim kurar. Acilen devre dışı bırakıp SSH kullanın.")

            if port == 161 and protocol == "UDP":
                recommendations.append("Bilgi: SNMP portu (161 UDP) açık. Varsayılan 'public' anahtarını kullanmadığınızdan emin olun.")

        score = min(100, score)

        if score == 0 and not open_ports: level = "🟢 Güvenli (Açık Port Yok)"
        elif score <= 25: level = "🟢 Düşük Risk"
        elif score <= 50: level = "🟡 Orta Risk"
        elif score <= 75: level = "🟠 Yüksek Risk"
        else: level = "🔴 Kritik Risk"

        if len(open_ports) > 0 and not recommendations:
            recommendations.append("Sistem genel olarak iyi yapılandırılmış görünüyor. Gereksiz servisleri kapatmayı unutmayın.")

        return {
            "total_score": score,
            "risk_level": level,
            "cve_alerts": cve_alerts,
            "recommendations": list(set(recommendations)),
            "processed_ports": open_ports
        }

# ==============================================================================
# 🚀 BÖLÜM 5: FASTAPI (REST API VE SUNUCU)
# ==============================================================================
app = FastAPI(
    title="ReconClaw v4.0 Ultimate API", 
    description="Asenkron Ağ Keşfi, Versiyon Tespiti, OSINT ve AI Risk Motoru",
    version="4.0"
)

class ScanRequest(BaseModel):
    target: str
    tcp_ports: List[int] = [21, 22, 23, 25, 53, 80, 110, 443, 3306, 3389, 5432, 8080]
    udp_ports: List[int] = [53, 123, 161]

@app.post("/api/v4/scan", tags=["Scanner"])
async def start_scan(req: ScanRequest):
    scanner = AsyncScanner(target=req.target, timeout=1.5)
    
    if not scanner.ip:
        raise HTTPException(status_code=400, detail="Hedef adres çözümlenemedi (DNS Hatası).")

    osint_data = scanner.get_osint_data()
    raw_results = await scanner.run_scan(tcp_ports=req.tcp_ports, udp_ports=req.udp_ports)
    analysis = AIBrain.analyze(raw_results)

    # Taramayı Veritabanına Kaydet
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO scan_history (target, ip_address, country, isp, open_ports_count, risk_score, risk_level, scan_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req.target, scanner.ip, osint_data.get('country'), osint_data.get('isp'), len(raw_results), analysis['total_score'], analysis['risk_level'], scan_time))
        
        scan_id = cursor.lastrowid
        for p in raw_results:
            cursor.execute('''
                INSERT INTO open_ports (scan_id, port, protocol, service, banner)
                VALUES (?, ?, ?, ?, ?)
            ''', (scan_id, p['port'], p['protocol'], p['service'], p['banner']))
            
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "status": "success",
        "target_info": {
            "domain": req.target,
            "resolved_ip": scanner.ip,
            "location": f"{osint_data.get('city', '')}, {osint_data.get('country', '')}".strip(', '),
            "isp": osint_data.get('isp', '')
        },
        "scan_summary": {
            "total_open_ports": len(raw_results),
            "risk_score": f"{analysis['total_score']}/100",
            "risk_level": analysis['risk_level']
        },
        "ai_analysis": {
            "cve_alerts": analysis['cve_alerts'],
            "recommendations": analysis['recommendations']
        },
        "port_details": analysis['processed_ports']
    }

@app.get("/api/v4/history", tags=["Database"])
def get_history():
    """Önceki taramaları (logları) SQLite'dan getirir"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, target, ip_address, country, isp, open_ports_count, risk_score, risk_level, scan_time FROM scan_history ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0], "target": row[1], "ip": row[2],
                "country": row[3], "isp": row[4], "open_ports": row[5],
                "risk_score": row[6], "risk_level": row[7], "date": row[8]
            })
        return {"history": history}
    except Exception as e:
        return {"error": str(e)}

@app.get("/", include_in_schema=False)
def home():
    return {"message": "🦅 ReconClaw v4.0 Ultimate Aktif! Test arayüzü için /docs adresine gidin."}

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*55}{Colors.RESET}")
    print(f" {Colors.BOLD}🦅 ReconClaw v4.0 Ultimate Başlatılıyor...{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*55}{Colors.RESET}")
    print(f" [{Colors.GREEN}✓{Colors.RESET}] SQLite Veritabanı Aktif")
    print(f" [{Colors.GREEN}✓{Colors.RESET}] Asenkron TCP & UDP Motoru Aktif")
    print(f" [{Colors.GREEN}✓{Colors.RESET}] OSINT (GeoIP/ASN) Engine Aktif")
    print(f" [{Colors.GREEN}✓{Colors.RESET}] AI Risk & CVE Motoru Aktif")
    print(f"{Colors.BLUE}{'='*55}{Colors.RESET}")
    print(f" 👉 {Colors.BOLD}TEST PANELİ:{Colors.RESET} http://127.0.0.1:8000/docs ")
    print(f" 👉 {Colors.BOLD}TARAMA GEÇMİŞİ:{Colors.RESET} http://127.0.0.1:8000/api/v4/history ")
    print(f"{Colors.BLUE}{'='*55}{Colors.RESET}\n")
    
    # Gereksiz logları kapatarak temiz ekran sunar
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
