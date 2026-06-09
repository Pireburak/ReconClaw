from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import os

app = FastAPI(title="ReconClaw AI Brain", version="0.2.0")

class ScanRequest(BaseModel):
    target: str

@app.get("/")
def index():
    return {"status": "online", "message": "ReconClaw Sinir Sistemi Aktif."}

@app.post("/api/scan")
def run_core_scan(req: ScanRequest):
    try:
        # Şimdi doğru yerde olduğumuz için ../core-engine mantığı kusursuz çalışacak
        core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core-engine'))
        
        result = subprocess.run(
            ["cargo", "run", "--quiet", "--", "--target", req.target],
            cwd=core_dir,
            capture_output=True,
            text=True
        )
        
        scan_data = json.loads(result.stdout)
        
        return {
            "success": True,
            "scan_results": scan_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
