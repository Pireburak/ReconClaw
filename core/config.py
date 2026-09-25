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

# Kullanıcı başına dakikada en fazla kaç tarama başlatılabilir (0 = sınırsız)
SCAN_RATE_LIMIT = int(env("SCAN_RATE_LIMIT", "10") or 0)
