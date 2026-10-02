"""
Abonelik planları: Free, Pro, Pro Max, Ultra, Ultra Max.

  * Limitler sunucu tarafında uygulanır (arayüzdeki kilitler yalnızca kolaylık içindir).
  * Günlük kullanım ayrı bir sayaçta tutulur; tarama silmek kotayı geri vermez.
  * Ödeme şimdilik "demo" modundadır: kart bilgisi istenmez ve saklanmaz, plan anında
    etkinleşir ve `payments` tablosuna "demo" durumlu bir kayıt düşülür. Gerçek ödeme
    altyapısı (iyzico, Lemon Squeezy vb.) `checkout()` fonksiyonunun yerine bağlanabilir.
"""

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta

from core.db_manager import get_db_connection

UNLIMITED = 0


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    level: int                 # "erişim seviyesi" 1..5
    tagline: str
    price_monthly: int         # TL
    daily_scans: int           # 0 = sınırsız
    per_minute: int            # dakikalık tarama sınırı, 0 = sınırsız
    max_port: int              # 1..max_port aralığı taranabilir
    plugins: bool              # HTTP başlık / TLS eklentileri
    exports: bool              # PDF ve CSV rapor
    compare: bool              # tarama karşılaştırma
    api: bool                  # API anahtarı
    targets: int               # doğrulanmış hedef sayısı, 0 = sınırsız

    @property
    def price_yearly(self) -> int:
        return self.price_monthly * 10  # yıllıkta 2 ay bedava

    def to_dict(self):
        data = asdict(self)
        data["price_yearly"] = self.price_yearly
        return data


PLANS = {p.id: p for p in (
    Plan("free", "Free", 1, "Keşfe başlamak için", 0,
         daily_scans=5, per_minute=2, max_port=100, plugins=False, exports=False, compare=False, api=False, targets=1),
    Plan("pro", "Pro", 2, "Düzenli denetim yapanlar için", 299,
         daily_scans=50, per_minute=5, max_port=1024, plugins=True, exports=True, compare=True, api=False, targets=3),
    Plan("pro_max", "Pro Max", 3, "Otomasyon ve API isteyenler için", 599,
         daily_scans=200, per_minute=10, max_port=10000, plugins=True, exports=True, compare=True, api=True, targets=10),
    Plan("ultra", "Ultra", 4, "Ekipler ve geniş ağlar için", 999,
         daily_scans=1000, per_minute=20, max_port=65535, plugins=True, exports=True, compare=True, api=True, targets=25),
    Plan("ultra_max", "Ultra Max", 5, "Sınırsız operasyon", 1999,
         daily_scans=UNLIMITED, per_minute=UNLIMITED, max_port=65535, plugins=True, exports=True, compare=True, api=True,
         targets=UNLIMITED),
)}
PERIODS = {"monthly": 30, "yearly": 365}


class PlanError(Exception):
    """Plan sınırı aşıldı; arayüz kullanıcıyı abonelik sayfasına yönlendirir (HTTP 402)."""


def _now():
    return datetime.now().replace(microsecond=0)


def effective_plan(user) -> Plan:
    """Kullanıcının şu an geçerli planı; süresi dolmuş ücretli plan Free sayılır."""
    plan = PLANS.get(user["plan"] or "free", PLANS["free"])
    if plan.id != "free" and user["plan_expires"] and user["plan_expires"] < _now().isoformat(" "):
        return PLANS["free"]
    return plan


def require(user, feature: str, message: str) -> Plan:
    plan = effective_plan(user)
    if not getattr(plan, feature):
        raise PlanError(message)
    return plan


def usage_today(user_id) -> int:
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT scans FROM usage WHERE user_id = ? AND day = ?",
                           (user_id, date.today().isoformat())).fetchone()
    return row["scans"] if row else 0


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


def record_scan(user_id):
    with closing(get_db_connection()) as conn, conn:
        conn.execute(
            "INSERT INTO usage (user_id, day, scans) VALUES (?, ?, 1) "
            "ON CONFLICT(user_id, day) DO UPDATE SET scans = scans + 1",
            (user_id, date.today().isoformat()),
        )


def checkout(user_id, plan_id: str, period: str = "monthly") -> dict:
    """Demo ödeme: planı anında etkinleştirir ve bir ödeme kaydı oluşturur."""
    plan = PLANS.get(plan_id)
    if plan is None or period not in PERIODS:
        raise ValueError("Geçersiz plan veya dönem.")
    now = _now()
    if plan.id == "free":
        expires, amount = None, 0
    else:
        expires = (now + timedelta(days=PERIODS[period])).isoformat(" ")
        amount = plan.price_yearly if period == "yearly" else plan.price_monthly
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET plan = ?, plan_expires = ? WHERE id = ?", (plan.id, expires, user_id))
        if amount:
            conn.execute(
                "INSERT INTO payments (user_id, plan, period, amount, currency, status, created_at) "
                "VALUES (?, ?, ?, ?, 'TRY', 'demo', ?)",
                (user_id, plan.id, period, amount, now.isoformat(" ")),
            )
    return {"plan": plan.id, "expires": expires, "amount": amount, "period": period, "mode": "demo"}


def payments(user_id, limit=20):
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            "SELECT id, plan, period, amount, currency, status, created_at FROM payments "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def subscription(user) -> dict:
    """Arayüz için plan, kullanım ve sınır özeti."""
    plan = effective_plan(user)
    expired = plan.id == "free" and (user["plan"] or "free") != "free"
    return {
        "plan": plan.to_dict(),
        "expires": None if plan.id == "free" else user["plan_expires"],
        "expired": expired,
        "usage": {"scans_today": usage_today(user["id"])},
    }
