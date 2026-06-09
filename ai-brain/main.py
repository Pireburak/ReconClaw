from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="ReconClaw AI Brain",
    description="Autonomous AI Security & OSINT Agent Backend",
    version="0.1.0"
)

# Kullanıcıdan gelecek mesaj şeması
class ChatMessage(BaseModel):
    message: str
    user_tier: str  # free, pro, ultra
    current_chat_count: int

@app.get("/")
def index():
    return {
        "status": "online",
        "agent": "ReconClaw AI Brain",
        "message": "Sistem aktif. Yolculuktaki azim için tebrikler!"
    }

@app.post("/api/chatops")
def handle_chatops(chat: ChatMessage):
    tier = chat.user_tier.lower()
    count = chat.current_chat_count

    # Yolda kurduğumuz o akıllı bütçe ve limit kontrol mekanizması
    if tier == "free" and count >= 15:
        raise HTTPException(status_code=403, detail="Free tier limitiniz doldu. Pro pakete geçiş yapın!")
    elif tier == "pro" and count >= 100:
        raise HTTPException(status_code=403, detail="Pro paket sohbet limitiniz doldu. Ultra pakete geçiş yapın!")
    elif tier == "ultra" and count >= 300:
        raise HTTPException(status_code=403, detail="Ultra paket aylık sohbet limitiniz dolmuştur.")

    # Yapay zeka ajanının ilk simüle cevabı
    return {
        "success": True,
        "tier": tier.upper(),
        "response": f"ReconClaw isteğinizi aldı: '{chat.message}'. Arka planda analiz tetikleniyor...",
        "remaining_chats": get_remaining_slots(tier, count)
    }

def get_remaining_slots(tier: str, count: int) -> int:
    limits = {"free": 15, "pro": 100, "ultra": 300}
    return max(0, limits.get(tier, 0) - count - 1)
