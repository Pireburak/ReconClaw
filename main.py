from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from core.db_manager import get_recent_scans, init_db, save_scan
from core.engine import COMMON_PORTS, AsyncScanner, RiskAnalyzer

VERSION = "4.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken veritabanı tablolarını kontrol et/oluştur
    init_db()
    yield


app = FastAPI(title=f"ReconClaw v{VERSION} Phantom", version=VERSION, lifespan=lifespan)

# Statik dosyalar (CSS, JS) ve HTML şablonları
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255, examples=["scanme.nmap.org"])
    # Verilmezse yaygın portlar taranır; verilirse 1..max_port aralığı taranır
    max_port: int | None = Field(None, ge=1, le=65535)
    timeout: float = Field(1.0, ge=0.2, le=5.0)


@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"title": "ReconClaw Dashboard", "version": VERSION}
    )


@app.post("/api/scan")
async def scan(req: ScanRequest):
    ports = range(1, req.max_port + 1) if req.max_port else COMMON_PORTS
    try:
        scanner = AsyncScanner(req.target, ports=ports, timeout=req.timeout)
        result = await scanner.run()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    analysis = RiskAnalyzer.analyze(result.open_ports)
    scan_id = await run_in_threadpool(save_scan, result.target, result.ip, analysis, result.duration)

    return {
        "success": True,
        "scan_id": scan_id,
        "target": result.target,
        "resolved_ip": result.ip,
        "scanned_ports": len(scanner.ports),
        "duration": result.duration,
        "total_open": len(analysis["ports"]),
        "overall_risk": analysis["score"],
        "risk_level": analysis["level"],
        "cve_alerts": analysis["cve_alerts"],
        "recommendations": analysis["recommendations"],
        "analysis": analysis["ports"],
    }


@app.get("/api/history")
async def history(limit: int = 20):
    return await run_in_threadpool(get_recent_scans, max(1, min(limit, 100)))


if __name__ == "__main__":
    print(f"\n🦅 ReconClaw v{VERSION} Phantom -> http://127.0.0.1:8000\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
