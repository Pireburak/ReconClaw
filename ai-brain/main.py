from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import json
import os
import sqlite3
import socket
from datetime import datetime

app = FastAPI(title="ReconClaw AI Brain", version="0.6.0")

# --- İÇ MİMARİ: Tesisatı (CSS ve JS dosyalarını) dış dünyaya açıyoruz ---
app.mount("/static", StaticFiles(directory="static"), name="static")

class ScanRequest(BaseModel):
    target: str
    max_port: int = 1000

def init_db():
    conn = sqlite3.connect("reconclaw.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            open_ports TEXT,
            scan_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- FAVICON DÜZELTMESİ: 404 Hatasını Susturan Kod ---
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# --- ANA SAYFA: JSON yerine HTML arayüzümüzü çağırır ---
@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/api/history")
def get_scan_history():
    try:
        conn = sqlite3.connect("reconclaw.db")
        cursor = conn.cursor()
        cursor.execute("SELECT target, open_ports, scan_time FROM scan_history ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        history_list = []
        for row in rows:
            history_list.append({
                "target": row[0],
                "open_ports": json.loads(row[1]),
                "scan_time": row[2]
            })
            
        return {"success": True, "history": history_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
def run_core_scan(req: ScanRequest):
    try:
        try:
            resolved_ip = socket.gethostbyname(req.target)
        except socket.gaierror:
            raise HTTPException(status_code=400, detail=f"Hata: '{req.target}' adresi çözümlenemedi. Geçerli bir adres girin.")

        core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core-engine'))
        
        result = subprocess.run(
            ["cargo", "run", "--quiet", "--", "--target", resolved_ip, "--max-port", str(req.max_port)],
            cwd=core_dir,
            capture_output=True,
            text=True
        )
        
        scan_data = json.loads(result.stdout)
        
        conn = sqlite3.connect("reconclaw.db")
        cursor = conn.cursor()
        ports_str = json.dumps(scan_data.get("open_ports", []))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        target_info = f"{req.target} ({resolved_ip})"
        
        cursor.execute(
            "INSERT INTO scan_history (target, open_ports, scan_time) VALUES (?, ?, ?)",
            (target_info, ports_str, timestamp)
        )
        conn.commit()
        conn.close()
        
        scan_data["resolved_ip"] = resolved_ip
        
        return {
            "success": True,
            "message": f"Sistem hedefi kilitledi: {req.target} -> {resolved_ip}",
            "scan_results": scan_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
