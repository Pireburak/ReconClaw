"""
Abonelik planları: Free, Pro, Pro Max, Ultra, Ultra Max (+ yalnızca yöneticilere açık sınırsız "Admin").

  * Limitler sunucu tarafında uygulanır (arayüzdeki kilitler yalnızca kolaylık içindir).
  * Günlük kullanım ayrı bir sayaçta tutulur; tarama silmek kotayı geri vermez.
  * Ödeme şimdilik "demo" modundadır: kart bilgisi istenmez ve saklanmaz, plan anında
    etkinleşir ve `payments` tablosuna "demo" durumlu bir kayıt düşülür. Gerçek ödeme
    altyapısı (iyzico, Lemon Squeezy vb.) `checkout()` fonksiyonunun yerine bağlanabilir.
"""

import secrets
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta

from core.db_manager import get_db_connection

UNLIMITED = 0


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    level: int                 # "erişim seviyesi" 1..5 (6 = yönetici)
    tagline: str
    price_monthly: int         # TL
    daily_scans: int           # 0 = sınırsız
    per_minute: int            # dakikalık tarama sınırı, 0 = sınırsız
    max_port: int              # 1..max_port aralığı taranabilir
    plugins: bool              # HTTP başlık / TLS eklentileri
    exports: bool              # PDF, CSV rapor ve paylaşım bağlantısı
    compare: bool              # tarama karşılaştırma
    api: bool                  # API anahtarı
    targets: int               # doğrulanmış hedef sayısı, 0 = sınırsız
    recon: bool = False        # v7.0 pasif keşif (alt alan adı, DNS, e-posta güvenliği)
    monitoring: bool = False   # v7.0 sürekli izleme
    monitors: int = 0          # izleme görevi sayısı, 0 = sınırsız (monitoring açıksa)
    hourly: bool = False       # saatlik izleme aralığı
    ai: bool = False           # v8.0 AI Analist
    ai_daily: int = 0          # günlük AI sorusu, 0 = sınırsız (ai açıksa)
    public: bool = True        # satın alınabilir planlar listesinde görünür

    @property
    def price_yearly(self) -> int:
        return self.price_monthly * 10  # yıllıkta 2 ay bedava

    def to_dict(self):
        data = asdict(self)
        data["price_yearly"] = self.price_yearly
        return data


PLANS = {p.id: p for p in (
    Plan("free", "Free", 1, "Keşfe başlamak için", 0,
         daily_scans=5, per_minute=2, max_port=100, plugins=False, exports=False, compare=False, api=False,
         targets=1),
    Plan("pro", "Pro", 2, "Düzenli denetim yapanlar için", 299,
         daily_scans=50, per_minute=5, max_port=1024, plugins=True, exports=True, compare=True, api=False,
         targets=3, recon=True, monitoring=True, monitors=1),
    Plan("pro_max", "Pro Max", 3, "Otomasyon, API ve AI analist", 599,
         daily_scans=200, per_minute=10, max_port=10000, plugins=True, exports=True, compare=True, api=True,
         targets=10, recon=True, monitoring=True, monitors=5, ai=True, ai_daily=20),
    Plan("ultra", "Ultra", 4, "Ekipler ve geniş ağlar için", 999,
         daily_scans=1000, per_minute=20, max_port=65535, plugins=True, exports=True, compare=True, api=True,
         targets=25, recon=True, monitoring=True, monitors=20, hourly=True, ai=True, ai_daily=100),
    Plan("ultra_max", "Ultra Max", 5, "Kurumsal ölçekte operasyon", 1999,
         daily_scans=5000, per_minute=60, max_port=65535, plugins=True, exports=True, compare=True, api=True,
         targets=100, recon=True, monitoring=True, monitors=50, hourly=True, ai=True, ai_daily=500),
)}

# Yalnızca yöneticilere verilen, satın alınamayan sınırsız seviye
ADMIN_PLAN = Plan("admin", "Admin", 6, "Sınırsız yönetici erişimi", 0,
                  daily_scans=UNLIMITED, per_minute=UNLIMITED, max_port=65535, plugins=True, exports=True,
                  compare=True, api=True, targets=UNLIMITED, recon=True, monitoring=True, monitors=UNLIMITED,
                  hourly=True, ai=True, ai_daily=UNLIMITED, public=False)
PERIODS = {"monthly": 30, "yearly": 365}


class PlanError(Exception):
    """Plan sınırı aşıldı; arayüz kullanıcıyı abonelik sayfasına yönlendirir (HTTP 402)."""


def _now():
    return datetime.now().replace(microsecond=0)


ADMIN_ROLES = ("admin", "owner")


def is_admin(user) -> bool:
    """Yönetici veya sahip (owner) mi? İkisi de sınırsız Admin seviyesindedir."""
    return user is not None and "role" in user.keys() and user["role"] in ADMIN_ROLES


def is_owner(user) -> bool:
    return user is not None and "role" in user.keys() and user["role"] == "owner"


def effective_plan(user) -> Plan:
    """Kullanıcının şu an geçerli planı; yöneticiler sınırsızdır, süresi dolmuş ücretli plan Free sayılır."""
    if is_admin(user):
        return ADMIN_PLAN
    plan = PLANS.get(user["plan"] or "free", PLANS["free"])
    if plan.id != "free" and user["plan_expires"] and user["plan_expires"] < _now().isoformat(" "):
        return PLANS["free"]
    return plan


def require(user, feature: str, message: str) -> Plan:
    plan = effective_plan(user)
    if not getattr(plan, feature):
        raise PlanError(message)
    return plan


def usage_today(user_id, column: str = "scans") -> int:
    assert column in ("scans", "ai")
    with closing(get_db_connection()) as conn:
        row = conn.execute(f"SELECT {column} FROM usage WHERE user_id = ? AND day = ?",
                           (user_id, date.today().isoformat())).fetchone()
    return row[column] if row else 0


def check_scan_quota(user, max_port: int | None) -> Plan:
    """Taramadan önce günlük kota ve port aralığını denetler."""
    plan = effective_plan(user)
    if max_port and max_port > plan.max_port:
        raise PlanError(f"{plan.name} planında en fazla 1–{plan.max_port} port aralığı taranabilir. "
                        f"Daha geniş aralık için planınızı yükseltin.")
    if plan.daily_scans != UNLIMITED and usage_today(user["id"]) >= plan.daily_scans:
        raise PlanError(f"{plan.name} planının günlük {plan.daily_scans} tarama hakkı doldu. "
                        f"Yarın tekrar deneyin veya planınızı yükseltin.")
    return plan


def record_scan(user_id, column: str = "scans"):
    assert column in ("scans", "ai")
    with closing(get_db_connection()) as conn, conn:
        conn.execute(
            f"INSERT INTO usage (user_id, day, {column}) VALUES (?, ?, 1) "
            f"ON CONFLICT(user_id, day) DO UPDATE SET {column} = {column} + 1",
            (user_id, date.today().isoformat()),
        )


def check_ai_quota(user) -> Plan:
    plan = require(user, "ai", "AI Analist Pro Max ve üzeri planlarda kullanılabilir.")
    if plan.ai_daily != UNLIMITED and usage_today(user["id"], "ai") >= plan.ai_daily:
        raise PlanError(f"{plan.name} planının günlük {plan.ai_daily} AI analiz hakkı doldu. "
                        f"Yarın tekrar deneyin veya planınızı yükseltin.")
    return plan


def checkout(user_id, plan_id: str, period: str = "monthly", region: dict | None = None) -> dict:
    """Demo ödeme: planı anında etkinleştirir ve bölgenin para biriminde bir ödeme kaydı oluşturur."""
    from core import pricing

    plan = PLANS.get(plan_id)
    if plan is None or period not in PERIODS:
        raise ValueError("Geçersiz plan veya dönem.")
    region = region or pricing.region_of("TR")
    now = _now()
    if plan.id == "free":
        expires, amount = None, 0
    else:
        expires = (now + timedelta(days=PERIODS[period])).isoformat(" ")
        amount = pricing.local_price(plan.price_monthly, region, yearly=period == "yearly")
    amount_try = pricing.to_try(amount, region["currency"]) if amount else 0
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET plan = ?, plan_expires = ? WHERE id = ?", (plan.id, expires, user_id))
        if amount:
            conn.execute(
                "INSERT INTO payments (user_id, plan, period, amount, currency, status, created_at, amount_try, country) "
                "VALUES (?, ?, ?, ?, ?, 'demo', ?, ?, ?)",
                (user_id, plan.id, period, amount, region["currency"], now.isoformat(" "), amount_try, region["country"]),
            )
    return {"plan": plan.id, "expires": expires, "amount": amount, "currency": region["currency"],
            "country": region["country"], "amount_try": amount_try, "period": period, "mode": "demo"}


def activate(user_id, plan_id: str, period: str) -> str:
    """Ödemesi onaylanan planı etkinleştirir. Aynı plan hâlâ geçerliyse süre kalan günün üstüne eklenir."""
    plan = PLANS[plan_id]
    now = _now()
    with closing(get_db_connection()) as conn, conn:
        row = conn.execute("SELECT plan, plan_expires FROM users WHERE id = ?", (user_id,)).fetchone()
        start = now
        if row and row["plan"] == plan.id and row["plan_expires"]:
            current = datetime.fromisoformat(row["plan_expires"])
            start = max(now, current)
        expires = (start + timedelta(days=PERIODS[period])).isoformat(" ")
        conn.execute("UPDATE users SET plan = ?, plan_expires = ? WHERE id = ?", (plan.id, expires, user_id))
    return expires


def create_pending(user_id, plan_id: str, period: str, region: dict) -> dict:
    """Gerçek ödeme başlamadan önce 'pending' durumlu bir sipariş kaydı oluşturur."""
    from core import pricing

    plan = PLANS.get(plan_id)
    if plan is None or plan.id == "free" or period not in PERIODS:
        raise ValueError("Geçersiz plan veya dönem.")
    amount = pricing.local_price(plan.price_monthly, region, yearly=period == "yearly")
    # PayTR sipariş numarası yalnızca harf ve rakam içerebilir (en fazla 64 karakter)
    oid = f"RC{user_id}T{int(_now().timestamp())}{secrets.token_hex(4).upper()}"
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO payments (user_id, plan, period, amount, currency, status, created_at, amount_try, country, "
            "merchant_oid, provider) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, 'paytr')",
            (user_id, plan.id, period, amount, region["currency"], _now().isoformat(" "),
             pricing.to_try(amount, region["currency"]), region["country"], oid))
    return {"id": cur.lastrowid, "user_id": user_id, "plan": plan, "period": period, "amount": amount,
            "currency": region["currency"], "merchant_oid": oid}


def complete_payment(merchant_oid: str, success: bool, paid_minor: int | None, note: str = "") -> dict | None:
    """Ödeme sağlayıcısının bildirimini işler. Aynı bildirim tekrar gelirse plan ikinci kez uzatılmaz.
    Döner: işlenen ödeme kaydı (yoksa None)."""
    with closing(get_db_connection()) as conn, conn:
        row = conn.execute("SELECT * FROM payments WHERE merchant_oid = ?", (merchant_oid,)).fetchone()
        if row is None:
            return None
        if row["status"] != "pending":
            return dict(row)  # zaten işlendi (PayTR bildirimi tekrarlayabilir)
        expected = int(round(row["amount"] * 100))
        if success and (paid_minor is None or paid_minor < expected):
            success, note = False, f"Tutar uyuşmuyor: beklenen {expected}, gelen {paid_minor}"
        status = "paid" if success else "failed"
        cur = conn.execute("UPDATE payments SET status = ?, paid_at = ?, note = ? WHERE id = ? AND status = 'pending'",
                           (status, _now().isoformat(" ") if success else None, note[:300], row["id"]))
        if cur.rowcount == 0:
            return {**dict(row), "status": "duplicate"}  # eşzamanlı tekrar bildirim
    if success:
        activate(row["user_id"], row["plan"], row["period"])
    return {**dict(row), "status": status}


def grant(user_id, plan_id: str, days: int | None = None) -> dict:
    """Yönetici ataması: ödeme kaydı oluşturmadan plan verir (days=None ise süresiz)."""
    plan = PLANS.get(plan_id)
    if plan is None:
        raise ValueError("Geçersiz plan.")
    expires = None if plan.id == "free" or not days else (_now() + timedelta(days=days)).isoformat(" ")
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET plan = ?, plan_expires = ? WHERE id = ?", (plan.id, expires, user_id))
    return {"plan": plan.id, "expires": expires}


def payments(user_id, limit=20):
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, plan, period, amount, currency, country, status, created_at, merchant_oid FROM payments "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def subscription(user) -> dict:
    """Arayüz için plan, kullanım ve sınır özeti."""
    plan = effective_plan(user)
    expired = plan.id == "free" and (user["plan"] or "free") != "free"
    return {
        "plan": plan.to_dict(),
        "expires": None if plan.id in ("free", "admin") else user["plan_expires"],
        "expired": expired,
        "admin": plan.id == "admin",
        "usage": {"scans_today": usage_today(user["id"]), "ai_today": usage_today(user["id"], "ai")},
    }
