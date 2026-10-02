import csv
import io
import ipaddress
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from urllib.parse import parse_qsl, quote

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from core import auth, config, oauth, plans, verify
from core.db_manager import (
    db_ok, delete_scans, get_recent_scans, get_scan_report, get_user_reports, init_db, save_scan,
)
from core.engine import COMMON_PORTS, AsyncScanner, RiskAnalyzer
from core.insights import build_stats, compare_reports
from core.plugins import available_plugins, enabled_names, run_plugins

VERSION = "6.1"
CODENAME = "Aurora"
STARTED_AT = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken veritabanı tablolarını kontrol et/oluştur
    init_db()
    yield


app = FastAPI(title=f"ReconClaw v{VERSION} {CODENAME}", version=VERSION, lifespan=lifespan)

# Statik dosyalar (CSS, JS) ve HTML şablonları
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _asset_version() -> str:
    """Statik dosyaların son değişiklik zamanından kısa bir sürüm etiketi üretir.
    Şablonlarda ?v=... olarak eklenir; dosya değişince tarayıcı eski CSS/JS'i önbellekten kullanmaz."""
    latest = 0.0
    for root, _, files in os.walk("static"):
        for name in files:
            latest = max(latest, os.path.getmtime(os.path.join(root, name)))
    return f"{VERSION}-{int(latest)}"


templates.env.globals["asset_v"] = _asset_version()

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; img-src 'self' data: https:; connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # ReconClaw'ın http_headers eklentisinin aradığı başlıkları kendi arayüzümüz de gönderir
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if not request.url.path.startswith(("/docs", "/redoc")):
        response.headers.setdefault("Content-Security-Policy", CSP)
    if config.COOKIE_SECURE:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.exception_handler(auth.AuthError)
async def auth_error_handler(request: Request, exc: auth.AuthError):
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(plans.PlanError)
async def plan_error_handler(request: Request, exc: plans.PlanError):
    # 402 Payment Required: arayüz kullanıcıyı abonelik sayfasına yönlendirir
    return JSONResponse({"detail": str(exc), "upgrade": True}, status_code=402)


@app.exception_handler(verify.VerifyError)
async def verify_error_handler(request: Request, exc: verify.VerifyError):
    return JSONResponse({"detail": str(exc)}, status_code=400)


# ---------------------------------------------------------------- yardımcılar
class RateLimiter:
    """Anahtar başına (kullanıcı / IP) kayan pencereli basit istek sınırlayıcı."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)

    def allow(self, key, limit: int | None = None) -> bool:
        limit = self.limit if limit is None else limit
        if limit <= 0:
            return True
        now, hits = time.monotonic(), self.hits[key]
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


scan_limiter = RateLimiter(config.SCAN_RATE_LIMIT, 60)
login_limiter = RateLimiter(10, 300)
active_scans = 0


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "?"


def _bearer(request: Request):
    header = request.headers.get("authorization", "")
    return header[7:].strip() if header.lower().startswith("bearer ") else None


def optional_user(request: Request):
    token = _bearer(request)
    if token:
        return auth.user_from_api_token(token)
    return auth.user_from_session(request.cookies.get(auth.SESSION_COOKIE))


def current_user(request: Request):
    user = optional_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Oturum açmanız gerekiyor.")
    if _bearer(request):
        plans.require(user, "api", "API erişimi Pro Max ve üzeri planlarda kullanılabilir.")
    return user


def start_session(response: Response, request: Request, user_id: int, remember: bool = True):
    days = config.SESSION_DAYS if remember else 1
    token = auth.create_session(user_id, request.headers.get("user-agent", ""), days=days)
    response.set_cookie(
        auth.SESSION_COOKIE, token, max_age=days * 86400 if remember else None,
        httponly=True, secure=config.COOKIE_SECURE, samesite="lax", path="/",
    )


def is_public_ip(ip: str) -> bool:
    return ipaddress.ip_address(ip).is_global


# ---------------------------------------------------------------- sayfalar
@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    user = optional_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "index.html", {
        "title": "ReconClaw | Operations Center", "version": VERSION, "codename": CODENAME,
        "user": auth.public_user(user),
    })


@app.get("/login", include_in_schema=False)
async def login_page(request: Request, error: str = ""):
    if optional_user(request) is not None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {
        "title": "ReconClaw | Giriş", "version": VERSION, "codename": CODENAME, "error": error[:200],
        "providers": oauth.provider_status(), "allow_signup": config.ALLOW_SIGNUP,
    })


@app.get("/reports/{scan_id}", include_in_schema=False)
async def printable_report(request: Request, scan_id: int):
    user = optional_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if not plans.effective_plan(user).exports:
        return RedirectResponse("/#plans", status_code=303)
    report = await run_in_threadpool(get_scan_report, scan_id, user["id"])
    if report is None:
        raise HTTPException(status_code=404, detail="Tarama raporu bulunamadı.")
    return templates.TemplateResponse(request, "report.html", {
        "title": f"ReconClaw Raporu #{scan_id} – {report['target']}", "version": VERSION,
        "r": report, "user": auth.public_user(user),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })


# ---------------------------------------------------------------- kimlik doğrulama
class Credentials(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=256)
    remember: bool = True


class Registration(Credentials):
    name: str = Field("", max_length=80)


@app.post("/auth/register", tags=["auth"])
async def register(body: Registration, request: Request, response: Response):
    if not login_limiter.allow(("register", client_ip(request))):
        raise HTTPException(status_code=429, detail="Çok fazla deneme. Birkaç dakika sonra tekrar deneyin.")
    user_id = await run_in_threadpool(auth.create_user, body.email, body.name, body.password)
    start_session(response, request, user_id, body.remember)
    return {"ok": True, "user": auth.public_user(auth.get_user(user_id))}


@app.post("/auth/login", tags=["auth"])
async def login(body: Credentials, request: Request, response: Response):
    if not login_limiter.allow(("login", client_ip(request))):
        raise HTTPException(status_code=429, detail="Çok fazla hatalı deneme. 5 dakika sonra tekrar deneyin.")
    user_id = await run_in_threadpool(auth.authenticate, body.email, body.password)
    start_session(response, request, user_id, body.remember)
    return {"ok": True, "user": auth.public_user(auth.get_user(user_id))}


@app.post("/auth/logout", tags=["auth"])
async def logout(request: Request, response: Response):
    auth.delete_session(request.cookies.get(auth.SESSION_COOKIE))
    response.delete_cookie(auth.SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/auth/providers", tags=["auth"])
async def providers():
    return oauth.provider_status()


@app.get("/auth/{provider}/login", include_in_schema=False)
async def oauth_login(provider: str, request: Request):
    p = oauth.PROVIDERS.get(provider)
    if p is None or not p.enabled:
        return RedirectResponse(f"/login?error={quote('Bu giriş yöntemi yapılandırılmamış.')}", status_code=303)
    state, verifier = oauth.new_state(provider)
    return RedirectResponse(p.authorize(oauth.redirect_uri(str(request.base_url), provider), state, verifier),
                            status_code=303)


@app.api_route("/auth/{provider}/callback", methods=["GET", "POST"], include_in_schema=False)
async def oauth_callback(provider: str, request: Request):
    p = oauth.PROVIDERS.get(provider)
    params = dict(request.query_params)
    form = {}
    if request.method == "POST":  # Apple form_post
        form = dict(parse_qsl((await request.body()).decode(errors="ignore")))
        params.update(form)
    try:
        if p is None or not p.enabled:
            raise oauth.OAuthError("Bu giriş yöntemi yapılandırılmamış.")
        verifier = oauth.consume_state(provider, params.get("state", ""))
        if "error" in params or "code" not in params:
            raise oauth.OAuthError("Giriş iptal edildi veya sağlayıcı izin vermedi.")
        redirect = oauth.redirect_uri(str(request.base_url), provider)
        info = await oauth.complete_login(p, params["code"], redirect, verifier, form)
        user_id = await run_in_threadpool(
            auth.login_with_identity, provider, info["subject"], info["email"], info["name"],
            info["email_verified"], info["avatar_url"],
        )
    except (oauth.OAuthError, auth.AuthError) as exc:
        return RedirectResponse(f"/login?error={quote(str(exc))}", status_code=303)
    response = RedirectResponse("/", status_code=303)
    start_session(response, request, user_id)
    return response


# ---------------------------------------------------------------- hesap
class ProfileUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class PasswordChange(BaseModel):
    current: str | None = Field(None, max_length=256)
    new: str = Field(..., max_length=256)


class AccountDelete(BaseModel):
    confirm_email: str


@app.get("/api/me", tags=["account"])
async def me(user=Depends(current_user)):
    data = auth.public_user(user)
    data["sessions"] = auth.count_sessions(user["id"])
    data["subscription"] = plans.subscription(user)
    return data


@app.patch("/api/me", tags=["account"])
async def update_me(body: ProfileUpdate, user=Depends(current_user)):
    auth.update_profile(user["id"], body.name)
    return auth.public_user(auth.get_user(user["id"]))


@app.post("/api/me/password", tags=["account"])
async def change_password(body: PasswordChange, request: Request, user=Depends(current_user)):
    await run_in_threadpool(auth.change_password, user["id"], body.current, body.new)
    # Parola değişince diğer cihazlardaki oturumlar kapatılır
    auth.delete_other_sessions(user["id"], request.cookies.get(auth.SESSION_COOKIE))
    return {"ok": True}


@app.post("/api/me/token", tags=["account"])
async def create_api_token(user=Depends(current_user)):
    plans.require(user, "api", "API anahtarı Pro Max ve üzeri planlarda kullanılabilir.")
    return {"token": auth.rotate_api_token(user["id"])}


@app.delete("/api/me/token", tags=["account"])
async def revoke_api_token(user=Depends(current_user)):
    auth.rotate_api_token(user["id"], revoke=True)
    return {"ok": True}


@app.post("/api/me/sessions/revoke", tags=["account"])
async def revoke_sessions(request: Request, user=Depends(current_user)):
    return {"revoked": auth.delete_other_sessions(user["id"], request.cookies.get(auth.SESSION_COOKIE))}


@app.delete("/api/me", tags=["account"])
async def delete_me(body: AccountDelete, response: Response, user=Depends(current_user)):
    if body.confirm_email.strip().lower() != user["email"].lower():
        raise HTTPException(status_code=400, detail="Onay için e-posta adresinizi doğru yazın.")
    auth.delete_user(user["id"])
    response.delete_cookie(auth.SESSION_COOKIE, path="/")
    return {"ok": True}


# ---------------------------------------------------------------- tarama
class ScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=255, examples=["scanme.nmap.org"])
    # Verilmezse yaygın portlar taranır; verilirse 1..max_port aralığı taranır
    max_port: int | None = Field(None, ge=1, le=65535)
    timeout: float = Field(1.0, ge=0.2, le=5.0)
    # Açık portlarda `plugins` dosyasındaki eklentileri çalıştır
    plugins: bool = True


@app.post("/api/scan", tags=["scan"])
async def scan(req: ScanRequest, user=Depends(current_user)):
    global active_scans
    plan = plans.check_scan_quota(user, req.max_port)
    per_minute = plan.per_minute
    if config.SCAN_RATE_LIMIT and (not per_minute or config.SCAN_RATE_LIMIT < per_minute):
        per_minute = config.SCAN_RATE_LIMIT  # sunucu genelindeki üst sınır
    if not scan_limiter.allow(user["id"], per_minute):
        raise HTTPException(status_code=429, detail=f"{plan.name} planında dakikada en fazla {per_minute} tarama başlatılabilir.")
    try:
        verify.ensure_allowed(user["id"], req.target)
    except verify.VerifyError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    started = time.perf_counter()
    ports = range(1, req.max_port + 1) if req.max_port else COMMON_PORTS
    try:
        scanner = AsyncScanner(req.target, ports=ports, timeout=req.timeout)
        await scanner.resolve()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not config.ALLOW_PRIVATE_TARGETS and not is_public_ip(scanner.ip):
        raise HTTPException(status_code=403, detail=f"İç ağ / özel adreslerin ({scanner.ip}) taranması bu sunucuda kapalı.")

    active_scans += 1
    try:
        result = await scanner.run()
        findings = []
        if req.plugins and plan.plugins and result.open_ports:
            findings = await run_plugins(result.target, result.ip, result.open_ports, timeout=max(req.timeout, 3.0))
    finally:
        active_scans -= 1
    analysis = RiskAnalyzer.analyze(result.open_ports, findings)

    report = {
        "success": True,
        "target": result.target,
        "resolved_ip": result.ip,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scanned_ports": len(scanner.ports),
        "duration": round(time.perf_counter() - started, 2),
        "total_open": len(analysis["ports"]),
        "overall_risk": analysis["score"],
        "risk_level": analysis["level"],
        "cve_alerts": analysis["cve_alerts"],
        "recommendations": analysis["recommendations"],
        "findings": analysis["findings"],
        "analysis": analysis["ports"],
    }
    report["scan_id"] = await run_in_threadpool(save_scan, report, user["id"])
    await run_in_threadpool(plans.record_scan, user["id"])
    return report


@app.get("/api/history", tags=["scan"])
async def history(limit: int = 20, q: str = "", user=Depends(current_user)):
    return await run_in_threadpool(get_recent_scans, max(1, min(limit, 200)), user["id"], q.strip()[:100])


@app.get("/api/scans/{scan_id}", tags=["scan"])
async def scan_detail(scan_id: int, user=Depends(current_user)):
    report = await run_in_threadpool(get_scan_report, scan_id, user["id"])
    if report is None:
        raise HTTPException(status_code=404, detail="Tarama raporu bulunamadı.")
    return report


@app.delete("/api/scans/{scan_id}", tags=["scan"])
async def scan_delete(scan_id: int, user=Depends(current_user)):
    if not await run_in_threadpool(delete_scans, user["id"], scan_id):
        raise HTTPException(status_code=404, detail="Tarama raporu bulunamadı.")
    return {"deleted": 1}


@app.delete("/api/scans", tags=["scan"])
async def scan_delete_all(user=Depends(current_user)):
    return {"deleted": await run_in_threadpool(delete_scans, user["id"])}


def _csv_cell(value):
    # Excel formül enjeksiyonunu önle: banner'lar uzak sunucudan gelir
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@app.get("/api/scans/{scan_id}/csv", tags=["scan"])
async def scan_csv(scan_id: int, user=Depends(current_user)):
    plans.require(user, "exports", "PDF ve CSV rapor Pro ve üzeri planlarda kullanılabilir.")
    report = await run_in_threadpool(get_scan_report, scan_id, user["id"])
    if report is None:
        raise HTTPException(status_code=404, detail="Tarama raporu bulunamadı.")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["tur", "port", "servis / eklenti", "siddet / risk", "baslik / banner", "aciklama"])
    for p in report["analysis"]:
        writer.writerow(map(_csv_cell, ["port", p["port"], p["service"], p["risk"], p["banner"], ""]))
    for f in report["findings"]:
        writer.writerow(map(_csv_cell, ["bulgu", f["port"], f["plugin"], f["severity"], f["title"], f["detail"]]))
    for alert in report["cve_alerts"]:
        writer.writerow(map(_csv_cell, ["cve", "", "", "critical", alert, ""]))
    filename = f"reconclaw-{report['target']}-{scan_id}.csv"
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/api/compare", tags=["scan"])
async def compare(old: int, new: int, user=Depends(current_user)):
    plans.require(user, "compare", "Tarama karşılaştırma Pro ve üzeri planlarda kullanılabilir.")
    a = await run_in_threadpool(get_scan_report, old, user["id"])
    b = await run_in_threadpool(get_scan_report, new, user["id"])
    if a is None or b is None:
        raise HTTPException(status_code=404, detail="Karşılaştırılacak taramalardan biri bulunamadı.")
    return compare_reports(a, b)


@app.get("/api/stats", tags=["dashboard"])
async def stats(user=Depends(current_user)):
    reports = await run_in_threadpool(get_user_reports, user["id"])
    data = build_stats(reports)
    data.update({
        "active_scans": active_scans,
        "db_status": "ONLINE" if db_ok() else "OFFLINE",
        "uptime": int(time.time() - STARTED_AT),
    })
    return data


# ---------------------------------------------------------------- abonelik
class CheckoutRequest(BaseModel):
    plan: str = Field(..., examples=["pro"])
    period: str = Field("monthly", pattern="^(monthly|yearly)$")


class TargetRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=255)


@app.get("/api/plans", tags=["billing"])
async def list_plans():
    return {"plans": [p.to_dict() for p in plans.PLANS.values()], "currency": "TRY", "payment_mode": "demo",
            "require_target_verification": config.REQUIRE_TARGET_VERIFICATION}


@app.get("/api/billing", tags=["billing"])
async def billing(user=Depends(current_user)):
    return {**plans.subscription(user), "payments": plans.payments(user["id"])}


@app.post("/api/billing/checkout", tags=["billing"])
async def billing_checkout(body: CheckoutRequest, user=Depends(current_user)):
    if body.plan not in plans.PLANS:
        raise HTTPException(status_code=422, detail="Geçersiz plan.")
    result = await run_in_threadpool(plans.checkout, user["id"], body.plan, body.period)
    return {**result, **plans.subscription(auth.get_user(user["id"]))}


@app.post("/api/billing/cancel", tags=["billing"])
async def billing_cancel(user=Depends(current_user)):
    await run_in_threadpool(plans.checkout, user["id"], "free")
    return plans.subscription(auth.get_user(user["id"]))


@app.get("/api/targets", tags=["billing"])
async def targets(user=Depends(current_user)):
    plan = plans.effective_plan(user)
    return {"targets": verify.list_targets(user["id"]), "limit": plan.targets,
            "required": config.REQUIRE_TARGET_VERIFICATION, "well_known": verify.WELL_KNOWN}


@app.post("/api/targets", tags=["billing"])
async def add_target(body: TargetRequest, user=Depends(current_user)):
    try:
        return await run_in_threadpool(verify.add_target, user, body.host)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/targets/{target_id}/verify", tags=["billing"])
async def verify_target(target_id: int, user=Depends(current_user)):
    return await verify.verify_target(user["id"], target_id)


@app.delete("/api/targets/{target_id}", tags=["billing"])
async def delete_target(target_id: int, user=Depends(current_user)):
    if not verify.delete_target(user["id"], target_id):
        raise HTTPException(status_code=404, detail="Hedef bulunamadı.")
    return {"deleted": 1}


@app.get("/api/plugins", tags=["scan"])
async def plugins():
    enabled = set(enabled_names())
    return [
        {"name": name, "description": cls.description, "ports": sorted(cls.ports), "enabled": name in enabled}
        for name, cls in available_plugins().items()
    ]


@app.get("/api/health", tags=["dashboard"])
async def health():
    return {"status": "ok", "version": VERSION, "db": db_ok(), "uptime": int(time.time() - STARTED_AT),
            "private_targets": config.ALLOW_PRIVATE_TARGETS,
            "target_verification": config.REQUIRE_TARGET_VERIFICATION}


if __name__ == "__main__":
    host, port = config.env("HOST", "127.0.0.1"), int(config.env("PORT", "8000"))
    print(f"\n🦝 ReconClaw v{VERSION} {CODENAME} -> http://{host}:{port}\n")
    uvicorn.run("main:app", host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")
