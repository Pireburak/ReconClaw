import asyncio
import socket
import sqlite3
import json
import urllib.request
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# ==============================================================================
# 1. BÖLÜM: MODELLER (Hata vermemesi için en başta tanımlıyoruz)
# ==============================================================================
class ScanRequest(BaseModel):
    target: str
    tcp_ports: List[int] = [21, 22, 23, 25, 53, 80, 110, 443, 3306, 3389, 5432, 8080]

# ==============================================================================
# 2. BÖLÜM: TERMİNAL RENKLERİ VE SQLITE VERİTABANI
# ==============================================================================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

DB_NAME = "reconclaw.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT NOT NULL,
            ip_address TEXT NOT NULL, country TEXT, isp TEXT,
            open_ports_count INTEGER, risk_score INTEGER, risk_level TEXT, scan_time TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS open_ports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, scan_id INTEGER, port INTEGER,
            protocol TEXT, service TEXT, banner TEXT, FOREIGN KEY(scan_id) REFERENCES scan_history(id))''')
        conn.commit()
        conn.close()
    except Exception: pass

init_db()

# ==============================================================================
# 3. BÖLÜM: CORE SCANNER ENGINE & AI BRAIN (Siber İstihbarat Motoru)
# ==============================================================================
class AsyncScanner:
    def __init__(self, target: str, timeout: float = 1.2):
        self.target = target
        self.timeout = timeout
        try: self.ip = socket.gethostbyname(target)
        except socket.gaierror: self.ip = None

    def get_osint_data(self):
        if not self.ip: return {"country": "Bilinmiyor", "isp": "Bilinmiyor", "city": "Bilinmiyor"}
        try:
            req = urllib.request.Request(f"http://ip-api.com/json/{self.ip}", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "success": return data
        except: pass
        return {"country": "Bilinmiyor", "isp": "Bilinmiyor", "city": "Bilinmiyor"}

    async def scan_tcp_port(self, port: int):
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(self.ip, port), timeout=self.timeout)
            banner = "Protected / No Banner"
            try:
                if port in [80, 443, 8080]: writer.write(b"HEAD / HTTP/1.1\r\nHost: " + self.ip.encode() + b"\r\n\r\n")
                else: writer.write(b"\r\n")
                await writer.drain()
                data = await asyncio.wait_for(reader.read(1024), timeout=0.8)
                if data: banner = data.decode('utf-8', errors='ignore').strip().split('\n')[0][:80]
            except: pass 
            finally:
                writer.close()
                await writer.wait_closed()
            return {"port": port, "protocol": "TCP", "state": "open", "banner": banner}
        except: return None 

    async def run_scan(self, tcp_ports: list):
        if not self.ip: return []
        tasks = [self.scan_tcp_port(port) for port in tcp_ports]
        results = await asyncio.gather(*tasks)
        return [res for res in results if res is not None]

class AIBrain:
    CRITICAL_PORTS = {21: ["FTP", 15], 22: ["SSH", 10], 23: ["Telnet", 25], 53: ["DNS", 5], 80: ["HTTP", 5], 443: ["HTTPS", 2], 3306: ["MySQL", 25], 3389: ["RDP", 20], 5432: ["PostgreSQL", 25], 8080: ["HTTP-Proxy", 10]}
    
    @classmethod
    def analyze(cls, open_ports: list):
        score, cve_alerts, recommendations = 0, [], []
        for item in open_ports:
            port = item['port']; banner = item.get('banner', '').lower()
            if port in cls.CRITICAL_PORTS:
                score += cls.CRITICAL_PORTS[port][1]
                item['service'] = cls.CRITICAL_PORTS[port][0]
            else:
                score += 2; item['service'] = "Unknown"

            if "openssh" in banner and any(v in banner for v in [" 4.", " 5.", " 6."]):
                score += 30; cve_alerts.append(f"[PORT {port}] Eski SSH Sürümü (CVE-2016-10009). RCE Riski!")
            if "apache/2.4.49" in banner or "apache/2.4.50" in banner:
                score += 50; cve_alerts.append(f"[PORT {port}] Kritik Apache Path Traversal (CVE-2021-41773).")
            if port in [3306, 5432, 1433]:
                recommendations.append(f"Kritik İhlal: Veritabanı portu ({port}) dış ağa açık. İç ağa izole edin!")
            if port == 23:
                recommendations.append(f"Kritik İhlal: Telnet (23) şifresiz iletişim kurar. Acilen kapatın ve SSH kullanın.")

        score = min(100, score)
        if score == 0 and not open_ports: level = "🟢 GÜVENLİ"
        elif score <= 25: level = "🟢 DÜŞÜK RİSK"
        elif score <= 50: level = "🟡 ORTA RİSK"
        elif score <= 75: level = "🟠 YÜKSEK RİSK"
        else: level = "🔴 KRİTİK RİSK"

        if len(open_ports) > 0 and not recommendations: recommendations.append("Gereksiz portları güvenlik duvarından engelleyin ve sistemleri güncel tutun.")
        return {"total_score": score, "risk_level": level, "cve_alerts": cve_alerts, "recommendations": recommendations, "processed_ports": open_ports}

# ==============================================================================
# 🚀 BÖLÜM 4: FASTAPI VE EN AFİLLİ MATRIX ARAYÜZÜ (HTML)
# ==============================================================================
# /docs kapatıldı, sadece havalı arayüz var!
app = FastAPI(title="ReconClaw v4.0 Ultimate", docs_url=None, redoc_url=None) 

@app.post("/api/v4/scan")
async def start_scan(req: ScanRequest):
    scanner = AsyncScanner(target=req.target, timeout=1.5)
    if not scanner.ip: raise HTTPException(status_code=400, detail="DNS Çözümlenemedi!")
    
    osint_data = scanner.get_osint_data()
    raw_results = await scanner.run_scan(tcp_ports=req.tcp_ports)
    analysis = AIBrain.analyze(raw_results)

    try:
        conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
        cursor.execute('INSERT INTO scan_history (target, ip_address, country, isp, open_ports_count, risk_score, risk_level, scan_time) VALUES (?,?,?,?,?,?,?,?)',
                       (req.target, scanner.ip, osint_data.get('country'), osint_data.get('isp'), len(raw_results), analysis['total_score'], analysis['risk_level'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
    except: pass

    return {
        "target_info": {"resolved_ip": scanner.ip, "location": f"{osint_data.get('city', '')}, {osint_data.get('country', '')}", "isp": osint_data.get('isp', '')},
        "scan_summary": {"risk_score": f"{analysis['total_score']}/100", "risk_level": analysis['risk_level']},
        "ai_analysis": {"cve_alerts": analysis['cve_alerts'], "recommendations": analysis['recommendations']},
        "port_details": analysis['processed_ports']
    }


PROFESSIONAL_MATRIX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReconClaw v4.0 Ultimate</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        :root { --primary: #0f0; --bg: #030303; --panel: rgba(0, 15, 0, 0.75); --danger: #ff003c; --warning: #ffb000; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Share Tech Mono', monospace; }
        body { background-color: var(--bg); color: var(--primary); overflow-x: hidden; }

        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: var(--primary); }

        /* MATRIX BG */
        #matrixCanvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; opacity: 0.25; }

        /* BOOT SCREEN */
        #loader { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #000; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999; transition: opacity 0.5s; }
        .radar { width: 120px; height: 120px; border-radius: 50%; border: 2px solid var(--primary); position: relative; background: repeating-radial-gradient(transparent, transparent 20px, rgba(0,255,0,0.1) 20px, rgba(0,255,0,0.1) 22px); box-shadow: 0 0 30px rgba(0, 255, 0, 0.4); margin-bottom: 30px; }
        .radar::before { content: ''; position: absolute; top: 50%; left: 50%; width: 60px; height: 60px; background: linear-gradient(45deg, var(--primary) 0%, transparent 60%); transform-origin: top left; animation: scan 1.5s linear infinite; }
        @keyframes scan { 100% { transform: rotate(360deg); } }
        .glitch-text { font-size: 2rem; letter-spacing: 5px; text-shadow: 2px 2px var(--danger), -2px -2px #00f; animation: glitch 0.5s infinite; }
        @keyframes glitch { 0% { transform: translate(0) } 20% { transform: translate(-2px, 2px) } 40% { transform: translate(-2px, -2px) } 60% { transform: translate(2px, 2px) } 80% { transform: translate(2px, -2px) } 100% { transform: translate(0) } }

        /* MAIN DASHBOARD */
        .container { max-width: 1100px; margin: 0 auto; padding: 30px 20px; display: none; }
        header { text-align: center; margin-bottom: 40px; border-bottom: 1px dashed var(--primary); padding-bottom: 20px; }
        header h1 { font-size: 3.5rem; text-shadow: 0 0 15px var(--primary); letter-spacing: 2px; }
        header p { color: #88ff88; font-size: 1.2rem; margin-top: 10px; }

        .panel { background: var(--panel); border: 1px solid var(--primary); padding: 25px; margin-bottom: 25px; box-shadow: 0 0 20px rgba(0,255,0,0.1); backdrop-filter: blur(8px); position: relative; }
        .panel::before { content:''; position:absolute; top:0; left:0; width:15px; height:15px; border-top:2px solid var(--primary); border-left:2px solid var(--primary); }
        .panel::after { content:''; position:absolute; bottom:0; right:0; width:15px; height:15px; border-bottom:2px solid var(--primary); border-right:2px solid var(--primary); }
        .panel h2 { border-bottom: 1px dashed var(--primary); padding-bottom: 10px; margin-bottom: 20px; text-transform: uppercase; font-size: 1.3rem; }

        .input-group { display: flex; gap: 15px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; background: #000; border: 1px solid var(--primary); color: var(--primary); padding: 15px; font-size: 1.3rem; outline: none; box-shadow: inset 0 0 10px rgba(0,255,0,0.2); transition: 0.3s; }
        input[type="text"]:focus { box-shadow: inset 0 0 20px rgba(0,255,0,0.6); }
        button { background: var(--primary); color: #000; border: none; padding: 0 35px; font-size: 1.3rem; font-weight: bold; cursor: pointer; transition: 0.3s; text-transform: uppercase; }
        button:hover { background: #fff; box-shadow: 0 0 25px var(--primary); }
        button:disabled { background: #222; color: #555; cursor: not-allowed; box-shadow: none; }

        /* LIVE TERMINAL */
        .terminal { background: #000; padding: 15px; border: 1px solid #333; height: 180px; overflow-y: auto; font-size: 1.1rem; }
        .terminal p { margin: 5px 0; }
        .t-time { color: #555; margin-right: 10px; }
        .t-msg { color: #0ff; } .t-warn { color: var(--warning); } .t-err { color: var(--danger); text-shadow: 0 0 5px var(--danger); } .t-succ { color: var(--primary); font-weight: bold; }

        /* RESULTS AREA */
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        .score-box { text-align: center; display: flex; flex-direction: column; justify-content: center; transition: 0.5s; }
        .score-box h1 { font-size: 5.5rem; margin: 10px 0; text-shadow: 0 0 20px var(--primary); }
        .critical { border-color: var(--danger) !important; box-shadow: inset 0 0 30px rgba(255,0,60,0.2) !important; }
        .critical-text { color: var(--danger) !important; text-shadow: 0 0 20px var(--danger) !important; }
        .high { border-color: var(--warning) !important; box-shadow: inset 0 0 30px rgba(255,176,0,0.1) !important; }
        .high-text { color: var(--warning) !important; text-shadow: 0 0 20px var(--warning) !important; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #0f0; padding: 12px; text-align: left; }
        th { background: rgba(0,255,0,0.2); font-size: 1.1rem; }
        tr:hover { background: rgba(0,255,0,0.1); }
        
        .vuln-box { border-left: 4px solid var(--danger); background: rgba(255,0,60,0.1); padding: 15px; margin-top: 20px; }
        .rec-box { border-left: 4px solid #0ff; background: rgba(0,255,255,0.05); padding: 15px; margin-top: 20px; }
        ul { margin-left: 20px; }
        li { margin-bottom: 8px; font-size: 1.1rem; }
    </style>
</head>
<body onload="bootSequence()">

    <canvas id="matrixCanvas"></canvas>

    <!-- PRO BOOT SCREEN -->
    <div id="loader">
        <div class="radar"></div>
        <div class="glitch-text" id="bootText">SYSTEM INITIALIZING...</div>
    </div>

    <div class="container" id="mainUI">
        <header>
            <h1>[ RECONCLAW ULTIMATE ]</h1>
            <p>ADVANCED NETWORK PORT SCANNER & AI THREAT INTELLIGENCE</p>
        </header>

        <div class="panel">
            <h2>> ADVANCED_PORT_SCANNER</h2>
            <div class="input-group">
                <input type="text" id="target" placeholder="Target Domain / IP (e.g. scanme.nmap.org)">
                <button id="scanBtn" onclick="executeScan()">START SCANNING</button>
            </div>
            <div class="terminal" id="terminal">
                <p><span class="t-time">[SYS]</span><span class="t-msg"> ReconClaw Scanner v4.0 is online. Waiting for parameters...</span></p>
            </div>
        </div>

        <div id="resultsArea" style="display: none; animation: fadeIn 1s;">
            <div class="grid">
                <!-- RISK PANEL -->
                <div class="panel score-box" id="scorePanel">
                    <h2 style="border:none;">AI RISK ASSESSMENT</h2>
                    <h1 id="riskScore">0</h1>
                    <h2 id="riskLevel">SECURE</h2>
                </div>

                <!-- TARGET INTEL PANEL -->
                <div class="panel">
                    <h2>> OSINT_FOOTPRINT</h2>
                    <p style="margin-bottom:15px;"><strong style="color:#888;">RESOLVED IP :</strong> <span id="r-ip" style="font-size:1.3rem;"></span></p>
                    <p style="margin-bottom:15px;"><strong style="color:#888;">GEOLOCATION :</strong> <span id="r-loc" style="font-size:1.3rem;"></span></p>
                    <p><strong style="color:#888;">DATACENTER  :</strong> <span id="r-isp" style="font-size:1.3rem;"></span></p>
                </div>
            </div>

            <!-- PORT TABLE -->
            <div class="panel">
                <h2>> DETECTED_OPEN_PORTS</h2>
                <table>
                    <thead><tr><th>PORT</th><th>PROTO</th><th>SERVICE</th><th>BANNER / VULN_SIGNATURE</th></tr></thead>
                    <tbody id="portTable"></tbody>
                </table>
            </div>

            <!-- AI ALERTS -->
            <div class="grid" id="ai-blocks">
                <div class="panel vuln-box">
                    <h2 style="color:var(--danger); border-color:var(--danger);">🔴 CRITICAL THREATS (CVE)</h2>
                    <ul id="vulnList" style="color:var(--danger);"></ul>
                </div>
                <div class="panel rec-box">
                    <h2 style="color:#0ff; border-color:#0ff;">🧠 AI RECOMMENDATIONS</h2>
                    <ul id="recList" style="color:#0ff;"></ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        // MATRIX BACKGROUND EFFECT
        const canvas = document.getElementById('matrixCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth; canvas.height = window.innerHeight;
        const letters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^&*'.split('');
        const fontSize = 14; const columns = canvas.width / fontSize;
        const drops = []; for(let i=0; i<columns; i++) drops[i] = 1;
        
        setInterval(() => {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#0F0'; ctx.font = fontSize + 'px monospace';
            for(let i=0; i<drops.length; i++) {
                const text = letters[Math.floor(Math.random() * letters.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
        }, 33);

        // BOOT SCREEN LOGIC
        function bootSequence() {
            const texts = ["ANALYZING NETWORK TOPOLOGY...", "INITIALIZING AI THREAT ENGINE...", "SYSTEM READY."];
            let i = 0;
            const bootInt = setInterval(() => {
                if(i < texts.length) { document.getElementById('bootText').innerText = texts[i]; i++; }
                else {
                    clearInterval(bootInt);
                    document.getElementById('loader').style.opacity = '0';
                    setTimeout(() => {
                        document.getElementById('loader').style.display = 'none';
                        document.getElementById('mainUI').style.display = 'block';
                    }, 500);
                }
            }, 900);
        }

        // TERMINAL LOGGER
        function logTerm(msg, type="msg") {
            const term = document.getElementById('terminal');
            const time = new Date().toLocaleTimeString('en-US', { hour12: false });
            term.innerHTML += `<p><span class="t-time">[${time}]</span><span class="t-${type}"> ${msg}</span></p>`;
            term.scrollTop = term.scrollHeight;
        }

        // EXECUTE SCAN API CALL
        async function executeScan() {
            const target = document.getElementById('target').value.trim();
            if(!target) return alert("System Error: Target Field Cannot Be Empty!");

            const btn = document.getElementById('scanBtn');
            btn.disabled = true; btn.innerText = "PROBING PORTS...";
            document.getElementById('resultsArea').style.display = 'none';
            document.getElementById('terminal').innerHTML = '';
            
            logTerm(`Target defined: ${target}`, 'warn');
            logTerm(`Resolving DNS & Extracting OSINT footprints...`, 'msg');
            
            setTimeout(() => logTerm(`Deploying Asynchronous TCP Socket Engine...`, 'msg'), 800);
            setTimeout(() => logTerm(`Sending probes for Banner Grabbing...`, 'msg'), 1600);

            try {
                const res = await fetch('/api/v4/scan', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({target: target, tcp_ports: [21, 22, 23, 25, 53, 80, 110, 443, 3306, 3389, 5432, 8080]})
                });
                const data = await res.json();
                
                if(data.detail) throw new Error(data.detail);

                logTerm(`Scan Complete! Found ${data.port_details.length} open ports.`, 'succ');
                logTerm(`AI Risk analysis Engine finished processing.`, 'succ');
                
                populateResults(data);

            } catch (err) {
                logTerm(`CRITICAL ERROR: ${err.message}`, 'err');
            } finally {
                btn.disabled = false; btn.innerText = "START SCANNING";
            }
        }

        // RESULTS POPULATOR
        function populateResults(data) {
            document.getElementById('r-ip').innerText = data.target_info.resolved_ip;
            document.getElementById('r-loc').innerText = data.target_info.location;
            document.getElementById('r-isp').innerText = data.target_info.isp;

            const scorePanel = document.getElementById('scorePanel');
            const rScore = document.getElementById('riskScore');
            const rLevel = document.getElementById('riskLevel');
            
            scorePanel.className = "panel score-box";
            rScore.className = ""; rLevel.className = "";
            
            if(data.scan_summary.risk_level.includes("KRİTİK")) {
                scorePanel.classList.add("critical"); rScore.classList.add("critical-text"); rLevel.classList.add("critical-text");
            } else if(data.scan_summary.risk_level.includes("YÜKSEK")) {
                scorePanel.classList.add("high"); rScore.classList.add("high-text"); rLevel.classList.add("high-text");
            }

            rScore.innerText = data.scan_summary.risk_score.split('/')[0];
            rLevel.innerText = data.scan_summary.risk_level;

            const tbody = document.getElementById('portTable');
            if(data.port_details.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#ffb000;">Hedefte açık port bulunamadı veya IDS/IPS engelliyor.</td></tr>';
            } else {
                tbody.innerHTML = data.port_details.map(p => `<tr><td><b style="color:#fff;">${p.port}</b></td><td style="color:#aaa;">${p.protocol}</td><td style="color:#ffb000;">${p.service}</td><td style="color:#0ff;">${p.banner}</td></tr>`).join('');
            }

            document.getElementById('vulnList').innerHTML = data.ai_analysis.cve_alerts.length ? data.ai_analysis.cve_alerts.map(a => `<li>${a}</li>`).join('') : '<li style="color:#0f0; list-style:none;">🟢 Kritik bir Zafiyet (CVE) tespit edilmedi.</li>';
            document.getElementById('recList').innerHTML = data.ai_analysis.recommendations.length ? data.ai_analysis.recommendations.map(r => `<li>${r}</li>`).join('') : '<li style="color:#0f0; list-style:none;">🟢 Sistem yapılandırması harika görünüyor.</li>';

            document.getElementById('resultsArea').style.display = 'block';
            document.getElementById('resultsArea').scrollIntoView({behavior: "smooth"});
        }
        
        document.getElementById("target").addEventListener("keypress", (e) => { if (e.key === "Enter") executeScan(); });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_gui():
    return PROFESSIONAL_MATRIX_HTML

if __name__ == "__main__":
    print(f"\n{Colors.GREEN}{'='*55}{Colors.RESET}")
    print(f" {Colors.BOLD}🦅 RECONCLAW v4.0 ULTIMATE (MATRIX EDITION) AKTİF!{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*55}{Colors.RESET}")
    print(f" 👉 {Colors.BOLD}Lütfen şov için tarayıcıdan doğrudan şu adrese gidin:{Colors.RESET}")
    print(f" 🌐 {Colors.GREEN}{Colors.BOLD}http://127.0.0.1:8000{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*55}{Colors.RESET}\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
