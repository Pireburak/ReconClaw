from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from core.db_manager import init_db

# Uygulama başlarken veritabanı tablolarını kontrol et/oluştur
init_db()

app = FastAPI(title="ReconClaw v4.0 Phantom")

# Statik dosyaları (CSS, JS, Resimler) sisteme tanıtıyoruz
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML şablonlarının nerede olduğunu belirtiyoruz
templates = Jinja2Templates(directory="templates")

# Ana sayfa rotası (Tarayıcıda localhost'a girildiğinde çalışacak kısım)
@app.get("/")
async def read_root(request: Request):
    # index.html sayfasını ekrana basıyoruz
    return templates.TemplateResponse("index.html", {"request": request, "title": "ReconClaw Dashboard"})
