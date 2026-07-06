from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import socket, sqlite3, asyncio
from datetime import datetime

app = FastAPI(title="ReconClaw v4.0 Phantom")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon(): 
    return Response(status_code=204)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

def init_db():
    conn = sqlite3.connect("reconclaw_v4.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scan_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, resolved_ip TEXT, risk_score INTEGER, scan_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

class ScanRequest(BaseModel):
    target: str
    max_port: int = 1024

services_map = {
    21: ("FTP (Zayıf Protokol)", 75), 22: ("SSH (Yönetim)", 50), 
    23: ("Telnet (Şifresiz)", 100), 25: ("SMTP (Mail)", 50), 
    53: ("DNS", 30), 80: ("HTTP (Web)", 30), 139: ("NetBIOS (Ağ)", 75), 
    443: ("HTTPS (Güvenli)", 30), 445: ("SMB (Kritik Dosya)", 100), 
    3306: ("MySQL (DB)", 75), 3389: ("RDP (Uzak Masaüstü)", 75)
}

async def scan_port(ip, port):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=0.5)
        banner = "Gizlenmiş/Yanıt Yok"
        
        if port in [21, 22, 25, 80]:
            if port == 80:
                writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
                await writer.drain()
            try:
                data = await asyncio.wait_for(reader.read(100), timeout=0.5)
                if data:
                    banner = data.decode('utf-8', errors='ignore').split('\n')[0].strip()[:35]
            except:
                pass
                
        writer.close()
        await writer.wait_closed()
        
        srv, risk = services_map.get(port, (f"Bilinmeyen (Port {port})", 30))
        # HATA BURADAYDI: risk_percentage olarak düzeltildi.
        return {"port": port, "service": srv, "risk_percentage": risk, "banner": banner}
    except:
        return None

@app.post("/api/scan")
async def run_phantom_scan(req: ScanRequest):
    try:
        try: resolved_ip = socket.gethostbyname(req.target)
        except socket.gaierror: raise HTTPException(status_code=400, detail="Hedef çözümlenemedi.")
        
        critical_ports = [21, 22, 23, 25, 53, 80, 139, 443, 445, 3306, 3389, 8080]
        ports_to_scan = [p for p in critical_ports if p <= req.max_port]
        
        tasks = [scan_port(resolved_ip, port) for port in ports_to_scan]
        results = await asyncio.gather(*tasks)
        
        analysis_data = [res for res in results if res is not None]
        
        total_risk = sum([item["risk_percentage"] for item in analysis_data])
        risk_score = min(int((total_risk / (len(analysis_data)*100+1))*100), 100) if analysis_data else 0
        
        conn = sqlite3.connect("reconclaw_v4.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO scan_logs (target, resolved_ip, risk_score, scan_date) VALUES (?, ?, ?, ?)", (req.target, resolved_ip, risk_score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        return {"success": True, "target": req.target, "resolved_ip": resolved_ip, "overall_risk": risk_score, "analysis": analysis_data, "total_open": len(analysis_data)}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=f"Sistem Hatası: {str(e)}")
