"""
ReconClaw ayarları.

Tüm ayarlar ortam değişkenlerinden okunur. Proje kökünde bir `.env` dosyası varsa
(bkz. `.env.example`) uygulama açılırken otomatik yüklenir; gerçek ortam
değişkenleri her zaman `.env` dosyasındakilerden önceliklidir.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv(path=os.path.join(BASE_DIR, ".env")):
    """Basit bir .env okuyucu: KEY=VALUE satırları, # ile başlayanlar yorumdur."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


load_dotenv()


def _bool(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on", "evet")


def env(name, default=""):
    return os.environ.get(name, default).strip()


# Sitenin dışarıdan erişilen adresi (ör. https://reconclaw.alanadiniz.com).
# OAuth yönlendirme adresleri bundan üretilir; boşsa istekteki adres kullanılır.
PUBLIC_URL = env("PUBLIC_URL").rstrip("/")

# Oturum çerezi yalnızca HTTPS üzerinden gönderilsin mi? (alan adında HTTPS ile yayındaysanız açın)
COOKIE_SECURE = _bool("COOKIE_SECURE", PUBLIC_URL.startswith("https://"))
SESSION_DAYS = int(env("SESSION_DAYS", "7") or 7)

# Yeni kullanıcı kaydına izin verilsin mi? Sadece siz kullanacaksanız hesabınızı açtıktan sonra kapatın.
ALLOW_SIGNUP = _bool("ALLOW_SIGNUP", True)

# 127.0.0.1, 10.x, 192.168.x gibi iç ağ adreslerinin taranmasına izin verilsin mi?
# Sunucu internete açıksa KAPATIN; aksi halde ziyaretçiler sunucunuzun iç ağını tarayabilir.
ALLOW_PRIVATE_TARGETS = _bool("ALLOW_PRIVATE_TARGETS", True)

# Dakikalık tarama sınırı abonelik planından gelir. Bu değer tüm planlar için ek bir
# sunucu geneli üst sınırdır (0 = kapalı, yalnızca plan sınırları geçerli).
SCAN_RATE_LIMIT = int(env("SCAN_RATE_LIMIT", "0") or 0)

# Yalnızca sahipliği kanıtlanmış (DNS TXT veya doğrulama dosyası) hedeflerin taranmasına izin ver.
# İnternete açık, herkesin kayıt olabildiği bir sunucuda AÇIN.
REQUIRE_TARGET_VERIFICATION = _bool("REQUIRE_TARGET_VERIFICATION", False)

# v7.0: yönetici hesapları. Virgülle ayrılmış e-postalar; bu hesaplar "Admin" olur: tüm plan
# sınırları kalkar ve Yönetim paneli açılır. Var olan hesaplar uygulama açılırken yükseltilir;
# kayıt anında ise yalnızca e-postası doğrulanmış sosyal giriş yönetici olur (bkz. auth.create_user).
# Örnek: ADMIN_EMAILS=ben@ornek.com,asistan@ornek.com
ADMIN_EMAILS = {e.strip().lower() for e in env("ADMIN_EMAILS").split(",") if e.strip()}

# Sistemin sahibi (owner): silinemez, askıya alınamaz, yetkisi alınamaz; yöneticileri yalnızca o çıkarabilir.
# Alternatif: python manage.py make-owner e-posta
OWNER_EMAIL = env("OWNER_EMAIL").lower()

# Sürekli izleme görevlerini çalıştıran arka plan zamanlayıcısı
SCHEDULER_ENABLED = _bool("SCHEDULER_ENABLED", True)

# v8.0: AI Analist. Anahtar yoksa kural tabanlı (çevrimdışı) analist kullanılır.
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
AI_MODEL = env("AI_MODEL", "claude-opus-5-5") or "claude-opus-5-5"

# v8.1: bölgesel fiyatlandırma. Türkiye dışındaki ziyaretçilere fiyat kendi para biriminde,
# aylık plan fiyatına bu kadar TL eklenerek gösterilir (Türkiye her zaman en ucuz).
REGIONAL_SURCHARGE_TRY = int(env("REGIONAL_SURCHARGE_TRY", "950") or 950)
# IP adresi bulunamazsa veya yerel ağdan bağlanılırsa kullanılacak ülke
DEFAULT_COUNTRY = (env("DEFAULT_COUNTRY", "TR") or "TR").upper()
# Ziyaretçi IP'sinin ülkesini çevrimiçi GeoIP servisiyle bul (ipapi.co, önbellekli)
GEO_LOOKUP = _bool("GEO_LOOKUP", True)
# Cloudflare arkasındaysanız CF-IPCountry başlığına güven (doğrudan erişimde açmayın, sahtelenebilir)
TRUST_COUNTRY_HEADER = _bool("TRUST_COUNTRY_HEADER", False)
# Kurları elle sabitlemek için (1 birim = kaç TL), ör: FX_RATES=USD=45,EUR=52,SAR=12
FX_RATES = env("FX_RATES")

# v8.2: Cloudflare Turnstile bot koruması (ikisi de doluysa giriş ve kayıtta doğrulama istenir)
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY")

# Cloudflare arkasındaysanız ziyaretçinin gerçek IP'sini CF-Connecting-IP başlığından al
# (ödeme sağlayıcısına ve hız sınırlarına giden IP). Doğrudan erişimde açmayın, sahtelenebilir.
TRUST_PROXY_IP = _bool("TRUST_PROXY_IP", TRUST_COUNTRY_HEADER)

# Demo ödeme: kart istenmeden plan anında açılır (yalnızca geliştirme / sunum için).
# HTTPS ile yayındaki sitede varsayılan olarak KAPALI; aksi halde herkes ücretli planları bedava alır.
# PayTR bağlıysa bu ayardan bağımsız olarak gerçek ödeme kullanılır.
DEMO_PAYMENTS = _bool("DEMO_PAYMENTS", not PUBLIC_URL.startswith("https://"))

# v9.0: PayTR iFrame API ile gerçek ödeme. Üçü de doluysa demo ödeme kapanır, PayTR açılır.
# Bilgiler: PayTR Mağaza Paneli → Destek & Kurulum → Entegrasyon Bilgileri
PAYTR_MERCHANT_ID = env("PAYTR_MERCHANT_ID")
PAYTR_MERCHANT_KEY = env("PAYTR_MERCHANT_KEY")
PAYTR_MERCHANT_SALT = env("PAYTR_MERCHANT_SALT")
# Mağaza canlıya alınana kadar 1 bırakın (test kartlarıyla denenir, para çekilmez)
PAYTR_TEST_MODE = _bool("PAYTR_TEST_MODE", True)
# PayTR adres ve telefon alanlarını zorunlu tutar; kullanıcıdan istenmediği için şirket bilgisi gönderilir
PAYTR_DEFAULT_ADDRESS = env("PAYTR_DEFAULT_ADDRESS") or env("COMPANY_ADDRESS") or "Türkiye"
PAYTR_DEFAULT_PHONE = env("PAYTR_DEFAULT_PHONE") or env("COMPANY_PHONE") or "05000000000"

# v9.0: yasal sayfalar (Mesafeli Satış Sözleşmesi, KVKK, İade…) ve iletişim sayfası bu bilgilerle dolar.
# Sanal POS başvurusunda bu sayfaların sitede yayında olması istenir.
COMPANY_NAME = env("COMPANY_NAME", "ReconClaw") or "ReconClaw"
COMPANY_TITLE = env("COMPANY_TITLE") or COMPANY_NAME          # ticari unvan / şahıs şirketi adı
COMPANY_ADDRESS = env("COMPANY_ADDRESS")
COMPANY_PHONE = env("COMPANY_PHONE")
COMPANY_EMAIL = env("COMPANY_EMAIL")
COMPANY_TAX_OFFICE = env("COMPANY_TAX_OFFICE")
COMPANY_TAX_NO = env("COMPANY_TAX_NO")
COMPANY_MERSIS = env("COMPANY_MERSIS")
COMPANY_KEP = env("COMPANY_KEP")

# v9.0: e-posta (şifre sıfırlama). SMTP_HOST boşsa "Şifremi unuttum" bağlantısı gizlenir.
SMTP_HOST = env("SMTP_HOST")
SMTP_PORT = int(env("SMTP_PORT", "587") or 587)
SMTP_USER = env("SMTP_USER")
SMTP_PASSWORD = env("SMTP_PASSWORD")
SMTP_FROM = env("SMTP_FROM") or SMTP_USER
SMTP_TLS = _bool("SMTP_TLS", True)   # 587: STARTTLS · 465 için SMTP_PORT=465 (SSL) kullanın
