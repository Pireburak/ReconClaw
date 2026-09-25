<h1 align="center">🦅 ReconClaw v5.0 Nebula</h1>

<p align="center"><b>Asenkron Ağ Keşfi, Port Tarama ve Risk Analiz Platformu</b></p>

<p align="center">
<img src="https://img.shields.io/badge/Version-v5.0%20Nebula-success?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
<img src="https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge" alt="License">
</p>

<p align="center">
<a href="#-v50-nebula-yenilikleri">Yenilikler</a> •
<a href="#-kurulum">Kurulum</a> •
<a href="#-kullanım">Kullanım</a> •
<a href="#-api">API</a> •
<a href="#-eklentiler">Eklentiler</a> •
<a href="#-risk-değerlendirme-modeli">Risk Modeli</a> •
<a href="#-alan-adında-yayınlama-https">Yayınlama</a> •
<a href="#-yol-haritası">Yol Haritası</a>
</p>

---

## 🚀 ReconClaw Nedir?

ReconClaw; **yetkili** ağ keşfi (reconnaissance), port analizi, servis tespiti ve ön güvenlik değerlendirmesi için geliştirilmiş, web arayüzlü bir siber güvenlik aracıdır.

Yalnızca açık portları listelemekle kalmaz:

- ⚡ **Asenkron TCP motoru** ile yüzlerce portu aynı anda, saniyeler içinde tarar
- 🔍 **Banner grabbing** ile çalışan servisin sürüm bilgisini yakalar
- 🧠 Açık servislerden **0–100 arası risk skoru** hesaplar
- 🔴 Bilinen zafiyetli sürümleri **CVE imzalarıyla** eşleştirir
- ✅ Her bulgu için **somut güvenlik önerileri** üretir
- 💾 Tüm taramaları **SQLite** veritabanına kaydeder ve geçmişi gösterir
- 🖥️ Sonuçları siber-operasyon merkezi görünümlü **web dashboard** üzerinde sunar
- 🔐 **E-posta/parola** veya **Google, GitHub, Microsoft, Apple** hesabıyla giriş
- 🌗 **Aydınlık / karanlık tema** ve telefonda da çalışan duyarlı tasarım

---

## ✨ v5.0 Nebula Yenilikleri

| # | Özellik | Açıklama |
|---|---------|----------|
| 1 | 🛰️ **Operations Center paneli** | Yan menülü yeni arayüz: tarana alan adı, zafiyet, kritik bulgu, yüksek riskli hedef, aktif tarama ve veritabanı durumu kartları; tehdit değerlendirme halkaları, **canlı güvenlik olay akışı**, zafiyet trend grafiği, en çok açık port grafiği, hedef risk tablosu, UTC saati ve çalışma süresi |
| 2 | 🌗 **Aydınlık / karanlık tema** | Üst çubuktaki butonla anında geçiş; Ayarlar'dan *Karanlık / Aydınlık / Sistem* seçimi. Tercih tarayıcıda saklanır |
| 3 | 🔐 **Kullanıcı girişi** | E-posta + parola ile kayıt/giriş (scrypt ile hash'lenir), **Google, GitHub, Microsoft ve Apple** ile tek tıkla giriş (OAuth 2.0 / OpenID Connect). Her kullanıcı yalnızca kendi taramalarını görür |
| 4 | ⇄ **Tarama karşılaştırma (Scan Diff)** | Aynı hedefin iki taramasını karşılaştırır: yeni açılan / kapanan portlar, sürümü değişen servisler, yeni ve çözülen bulgular/CVE'ler, risk değişimi |
| 5 | ◎ **Ağ haritası** | Hedefi ve açık servisleri riske göre renklenen bir topoloji grafiği olarak çizer; CVE'li bağlantılar kırmızı yanıp söner |
| 6 | 🖨️ **PDF & CSV rapor** | Yönetici özetli, yazdırılabilir rapor sayfası (tarayıcıdan *PDF olarak kaydet*) ve Excel'de açılabilen CSV dışa aktarımı |
| 7 | 🔑 **API anahtarı & hesap güvenliği** | Ayarlar'dan kişisel API anahtarı (`Authorization: Bearer rc_...`), parola değiştirme, diğer cihazlardan çıkış, geçmişi/hesabı silme |
| 8 | 🌐 **Alan adında yayın** | Docker + Caddy ile tek komutla otomatik HTTPS; iç ağ tarama engeli, tarama/giriş hız sınırı, güvenlik başlıkları (CSP, HSTS, X-Frame-Options) |

---

## ⚡ Özellikler

| Özellik                        | Durum | Özellik                     | Durum |
| ------------------------------ | :---: | --------------------------- | :---: |
| Asenkron TCP Connect Tarama    |  ✅   | Web Dashboard (responsive)  |  ✅   |
| DNS Çözümleme                  |  ✅   | REST API (JSON)             |  ✅   |
| Banner Grabbing / Sürüm Tespiti|  ✅   | Tarama Geçmişi (SQLite)     |  ✅   |
| Kural Tabanlı Risk Motoru      |  ✅   | CVE İmza Eşleştirme         |  ✅   |
| Yaygın Port / Aralık Taraması  |  ✅   | Otomatik Testler (pytest)   |  ✅   |
| Eklenti Sistemi                |  ✅   | TLS Sertifika Kontrolü      |  ✅   |
| HTTP Güvenlik Başlığı Kontrolü |  ✅   | JSON Rapor İndirme          |  ✅   |
| Kullanıcı Girişi & OAuth       |  ✅   | Aydınlık / Karanlık Tema    |  ✅   |
| Tarama Karşılaştırma           |  ✅   | Ağ Haritası                 |  ✅   |
| PDF / CSV Rapor                |  ✅   | API Anahtarı                |  ✅   |
| Docker + Otomatik HTTPS        |  ✅   | UDP Tarama                  |  🔜   |

---

## 📦 Kurulum

> Gereksinim: **Python 3.10+**

```bash
git clone https://github.com/Pireburak/ReconClaw.git
cd ReconClaw

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🖥️ Kullanım

Sunucuyu başlatın:

```bash
python main.py
# veya geliştirme modunda:
uvicorn main:app --reload
```

Ardından tarayıcıda **http://127.0.0.1:8000** adresini açın.

0. **Kayıt Ol** sekmesinden e-posta ve parola ile hesap açın (veya yapılandırdıysanız Google/GitHub/Microsoft/Apple ile girin). Kimlik doğrulama gelmeden önce yapılmış eski taramalar, ilk açılan hesaba otomatik aktarılır.
1. Sol menüden **[01] NEW_SCAN** sayfasına geçip hedef IP adresini veya alan adını girin (`https://site.com/yol` gibi girdiler otomatik temizlenir).
2. Port kapsamını seçin:
   - **Yaygın portlar** → güvenlik açısından kritik 27 port (FTP, SSH, SMB, RDP, veritabanları…)
   - **1 → Maks. port** → belirttiğiniz sınıra kadar tüm portlar (en fazla 65535)
3. **Eklentiler** kutusu işaretliyse açık web/TLS portlarında ek güvenlik kontrolleri de çalışır.
4. **TARAMAYI BAŞLAT** butonuna basın; sonuçlar, CVE uyarıları, eklenti bulguları ve öneriler anında ekrana gelir.
5. **[02] SCAN_RESULTS** sayfasında raporu **JSON / CSV / PDF** olarak indirin, **Önceki ile karşılaştır** veya **Ağ haritası** butonlarını kullanın.
6. **[03] SCAN_HISTORY**'de arama yapın, iki taramayı işaretleyip karşılaştırın; **[00] SYS_OVERVIEW** tüm taramalarınızın özetini gösterir.
7. Sağ üstteki 🌙/☀️ butonu ile temayı değiştirin; **[06] SETTINGS**'te tarama varsayılanları, parola ve API anahtarı ayarlanır.

Ayarlar ortam değişkenleri veya proje kökündeki `.env` dosyasıyla yapılır (`cp .env.example .env`). Tüm seçenekler `.env.example` içinde açıklamalıdır.

> 💡 Yasal ve güvenli test için Nmap'in resmi test sunucusu `scanme.nmap.org` kullanılabilir.

---

## 🔌 API

Etkileşimli API dokümantasyonu: **http://127.0.0.1:8000/docs**

Tüm `/api/*` uç noktaları oturum ister. Tarayıcıda giriş çerezi, script/curl için **Ayarlar → API_ACCESS**'ten oluşturulan anahtar kullanılır.

### `POST /api/scan`

```bash
curl -X POST http://127.0.0.1:8000/api/scan \
     -H "Authorization: Bearer rc_ANAHTARINIZ" \
     -H "Content-Type: application/json" \
     -d '{"target": "scanme.nmap.org"}'
```

| Alan       | Tip    | Zorunlu | Açıklama                                                     |
| ---------- | ------ | :-----: | ------------------------------------------------------------ |
| `target`   | string |   ✅    | IP adresi veya alan adı                                      |
| `max_port` | int    |   —     | Verilirse `1..max_port` taranır, verilmezse yaygın portlar   |
| `timeout`  | float  |   —     | Port başına bağlantı zaman aşımı (0.2 – 5 sn, varsayılan 1) |
| `plugins`  | bool   |   —     | Eklentileri çalıştır (varsayılan `true`)                     |

<details>
<summary>Örnek yanıt</summary>

```json
{
  "success": true,
  "scan_id": 12,
  "scan_time": "2026-09-25 10:15:42",
  "target": "example.com",
  "resolved_ip": "192.168.1.10",
  "scanned_ports": 27,
  "duration": 1.04,
  "total_open": 4,
  "overall_risk": 72,
  "risk_level": { "key": "high", "label": "Yüksek Risk" },
  "cve_alerts": [
    "[Port 22] Eski OpenSSH sürümü (CVE-2016-10009 vb.). Uzaktan kod çalıştırma riski."
  ],
  "recommendations": [
    "MySQL (3306) dış ağa açık. Yalnızca iç ağdan erişilebilir olmalı, IP filtrelemesi uygulayın.",
    "Kullanılmayan servisleri kapatın, yazılımları güncel tutun ve taramayı düzenli tekrarlayın."
  ],
  "findings": [
    { "plugin": "http_headers", "port": 80, "severity": "low", "title": "Sürüm ifşası: server: nginx/1.18.0", "detail": "Sunucu yapılandırmasında sürüm bilgisini gizleyin." }
  ],
  "analysis": [
    { "port": 22, "protocol": "TCP", "banner": "SSH-2.0-OpenSSH_5.3", "service": "SSH", "risk": 80 }
  ]
}
```
</details>

### Diğer uç noktalar

| Uç Nokta                    | Açıklama                                               |
| --------------------------- | ------------------------------------------------------ |
| `GET /api/history?limit=20&q=` | Son taramaların özet listesi (en yeniden eskiye, `q` ile hedef/IP araması) |
| `GET /api/scans/{id}`       | Kayıtlı bir taramanın tam raporu (`/api/scan` yanıtı ile aynı yapı) |
| `DELETE /api/scans/{id}`    | Bir taramayı siler (`DELETE /api/scans` tüm geçmişi siler) |
| `GET /api/scans/{id}/csv`   | Raporu CSV olarak indirir                               |
| `GET /reports/{id}`         | Yazdırılabilir / PDF'e kaydedilebilir rapor sayfası     |
| `GET /api/compare?old=1&new=2` | İki tarama arasındaki fark                           |
| `GET /api/stats`            | Dashboard istatistikleri, trend, olay akışı            |
| `GET /api/plugins`          | Mevcut eklentiler, çalıştıkları portlar ve etkin olup olmadıkları |
| `GET /api/me`, `PATCH /api/me` | Profil bilgisi / ad güncelleme                       |
| `POST /api/me/password`     | Parola değiştir / belirle                               |
| `POST /api/me/token`        | Yeni API anahtarı (`DELETE` ile iptal)                  |
| `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` | E-posta ile kayıt, giriş, çıkış |
| `GET /auth/{google\|github\|microsoft\|apple}/login` | Sosyal giriş             |
| `GET /api/health`           | Sağlık kontrolü (oturum gerektirmez)                   |

---

## 🧩 Eklentiler

Port taraması bittikten sonra eklentiler, ilgilendikleri açık portlarda ek kontroller yapar. Bulguların şiddetine göre (Yüksek +15, Orta +8, Düşük +3, Bilgi 0) ilgili portun ve hedefin risk skoru artar.

| Eklenti        | Portlar                          | Kontroller                                                                 |
| -------------- | -------------------------------- | -------------------------------------------------------------------------- |
| `http_headers` | 80, 443, 8000, 8008, 8080, 8443, 8888 | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy eksikliği; `Server` / `X-Powered-By` sürüm ifşası |
| `tls_cert`     | 443, 465, 636, 993, 995, 8443    | Sertifika doğrulama (kendinden imzalı, süresi dolmuş, isim uyuşmazlığı), 30 günden az kalan süre, TLS 1.0/1.1 kullanımı |

**Açma / kapatma:** Proje kökündeki `plugins` dosyasında her satır bir eklentidir. Kapatmak için satırın başına `#` koyun:

```text
http_headers
# tls_cert     <- kapalı
```

**Yeni eklenti yazmak:** `core/plugins/` altına bir modül ekleyin, `Plugin` sınıfından türetin ve adını `plugins` dosyasına yazın:

```python
from core.plugins import Plugin

class OrnekPlugin(Plugin):
    name = "ornek"
    description = "Örnek kontrol"
    ports = {8080}

    async def check(self, target, ip, port):
        return [self.finding(port, "low", "Başlık", "Açıklama")]
```

---

## 📊 Risk Değerlendirme Modeli

Her açık port, servisin kritikliğine göre bir **risk ağırlığı** taşır (ör. HTTPS: 2, SSH: 10, RDP: 20, Telnet / SMB / veritabanları: 25). Banner'da bilinen zafiyetli bir sürüm yakalanırsa ek puan eklenir. Toplam puan **100** ile sınırlandırılır.

| Risk Seviyesi  | Skor         | Durum     | Açıklama                                                                  |
| :------------- | :----------: | :-------: | ------------------------------------------------------------------------- |
| 🟢 Düşük Risk  | **0 – 25**   | Güvenli   | Kritik seviyede bir güvenlik riski bulunmamaktadır.                       |
| 🟡 Orta Risk   | **26 – 50**  | İzlenmeli | Yapılandırma iyileştirmeleri ve düzenli kontroller önerilir.              |
| 🟠 Yüksek Risk | **51 – 75**  | Riskli    | Açık servisler saldırı yüzeyini artırıyor; önlemler güçlendirilmelidir.   |
| 🔴 Kritik Risk | **76 – 100** | Kritik    | Kritik servisler veya bilinen zafiyetler tespit edildi; acil aksiyon alın. |

**Tanınan CVE imzaları:**

| Banner İmzası          | Zafiyet                                         |
| ---------------------- | ----------------------------------------------- |
| OpenSSH 4.x – 6.x      | CVE-2016-10009 ve benzeri eski sürüm açıkları   |
| Apache 2.4.49 / 2.4.50 | CVE-2021-41773 / CVE-2021-42013 (Path Traversal & RCE) |
| vsFTPd 2.3.4           | CVE-2011-2523 (arka kapı)                       |
| ProFTPD 1.3.0 – 1.3.5  | CVE-2015-3306 (mod_copy)                        |
| Microsoft-IIS 5 – 7    | Desteği bitmiş sürüm                            |

### 📌 Örnek Analiz

```text
═══════════════════════════════════════════════════════
 Hedef          : example.com
 Çözümlenen IP  : 192.168.1.10
───────────────────────────────────────────────────────
 Açık Portlar
   22/tcp    SSH      SSH-2.0-OpenSSH_5.3
   80/tcp    HTTP     nginx
   443/tcp   HTTPS
   3306/tcp  MySQL
───────────────────────────────────────────────────────
 Risk Skoru     : 72 / 100
 Risk Seviyesi  : 🟠 Yüksek Risk
───────────────────────────────────────────────────────
 Uyarılar & Öneriler
 ✘ [Port 22] Eski OpenSSH sürümü (CVE-2016-10009 vb.)
 ✔ MySQL (3306) portunu dış ağa kapatın, IP filtrelemesi uygulayın.
 ✔ Kullanılmayan servisleri kapatın, yazılımları güncel tutun.
═══════════════════════════════════════════════════════
```

> **Not:** Risk skoru hızlı bir **ön değerlendirmedir**; kapsamlı bir sızma testinin veya zafiyet taramasının yerini tutmaz.

---

## 🌐 Alan Adında Yayınlama (HTTPS)

Bir alan adı (ör. `alanadiniz.com`) ve bir sunucu (VPS) aldığınızda ReconClaw'ı tek komutla HTTPS üzerinden yayınlayabilirsiniz. [Caddy](https://caddyserver.com) Let's Encrypt'ten **ücretsiz SSL sertifikasını otomatik** alır ve yeniler.

```bash
# 1) DNS: alan adınızın (veya reconclaw.alanadiniz.com alt alanının) A kaydını sunucunun IP'sine yönlendirin
# 2) Sunucuda:
git clone https://github.com/Pireburak/ReconClaw.git && cd ReconClaw
cp .env.example .env
nano .env        # DOMAIN=reconclaw.alanadiniz.com
                 # PUBLIC_URL=https://reconclaw.alanadiniz.com
                 # ALLOW_PRIVATE_TARGETS=false   <- internete açık sunucuda mutlaka
docker compose up -d --build
```

Site `https://reconclaw.alanadiniz.com` adresinde açılır. İlk hesabınızı oluşturduktan sonra yabancıların kayıt olmasını istemiyorsanız `.env` içinde `ALLOW_SIGNUP=false` yapıp `docker compose up -d` ile yeniden başlatın.

### 🔐 Sosyal girişi açmak

Her sağlayıcıda bir "OAuth uygulaması" oluşturup verilen ID/secret değerlerini `.env` dosyasına yazmanız yeterli; doldurulmayan sağlayıcıların butonu pasif görünür.

| Sağlayıcı | Nereden alınır | Yönlendirme (callback) adresi | `.env` |
|-----------|----------------|-------------------------------|--------|
| Google    | [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) → *OAuth client ID (Web)* | `https://ALANADI/auth/google/callback` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| GitHub    | [GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers) | `https://ALANADI/auth/github/callback` | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Microsoft | [Microsoft Entra → App registrations](https://entra.microsoft.com) (*Web* platformu) | `https://ALANADI/auth/microsoft/callback` | `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` |
| Apple     | [Apple Developer](https://developer.apple.com/account/resources) → *Services ID* + *Sign in with Apple* anahtarı (.p8) — ücretli geliştirici hesabı gerekir | `https://ALANADI/auth/apple/callback` | `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY_PATH` |

> 💡 Google ve GitHub, yerel geliştirmede `http://127.0.0.1:8000/auth/.../callback` adresini de kabul eder; alan adı almadan önce deneyebilirsiniz. Apple yalnızca HTTPS alan adlarıyla çalışır.

### 🛡️ Güvenlik önlemleri

- Parolalar **scrypt** (tuzlu) ile saklanır; oturum anahtarları veritabanında yalnızca SHA-256 özetiyle tutulur, çerezler `HttpOnly` + `SameSite=Lax` (+ HTTPS'te `Secure`).
- OAuth akışında tek kullanımlık `state` (CSRF koruması) ve Google/Microsoft için **PKCE**; sosyal hesap, var olan bir hesaba yalnızca sağlayıcı e-postayı **doğrulamışsa** bağlanır (hesap ele geçirme koruması).
- Giriş denemeleri IP başına (10 / 5 dk), taramalar kullanıcı başına (`SCAN_RATE_LIMIT` / dk) sınırlandırılır.
- `ALLOW_PRIVATE_TARGETS=false` ile ziyaretçilerin sunucunuzun iç ağını (127.0.0.1, 10.x, 192.168.x) taraması engellenir.
- Arayüz; CSP, HSTS, X-Frame-Options, X-Content-Type-Options ve Referrer-Policy başlıklarını gönderir — yani ReconClaw'ın kendi `http_headers` eklentisinden temiz geçer.
- CSV dışa aktarımında Excel formül enjeksiyonuna karşı hücreler temizlenir.

---

## 🏗️ Sistem Mimarisi

```text
   🔐 Giriş (e-posta / Google / GitHub / Microsoft / Apple)
                     │  oturum çerezi / API anahtarı
                     ▼
        🌐 Web Dashboard (templates + static)
                     │  fetch /api/*
                     ▼
            ⚙️  FastAPI (main.py)  ── core/auth.py, core/oauth.py
                     │                 core/insights.py (istatistik, karşılaştırma)
                     │
        ┌────────────┼──────────────┐
        ▼            ▼              ▼
  AsyncScanner ──► core/plugins ──► RiskAnalyzer ──► db_manager
  (DNS + TCP +     (HTTP başlık,     (skor, CVE,      (SQLite:
   banner)          TLS sertifika)    öneriler)        geçmiş, rapor)
```

---

## 📂 Proje Yapısı

```text
ReconClaw/
├── main.py               # FastAPI uygulaması, sayfalar ve API uç noktaları
├── core/
│   ├── config.py         # .env / ortam değişkeni ayarları
│   ├── auth.py           # Kullanıcılar, parola hash'leme, oturumlar, API anahtarı
│   ├── oauth.py          # Google / GitHub / Microsoft / Apple girişi
│   ├── insights.py       # Dashboard istatistikleri + tarama karşılaştırma
│   ├── engine.py         # AsyncScanner + RiskAnalyzer
│   ├── db_manager.py     # SQLite bağlantısı, tablolar, kayıt işlemleri
│   └── plugins/          # Eklenti sistemi
│       ├── __init__.py   #   Plugin temel sınıfı, yükleyici
│       ├── http_headers.py
│       └── tls_cert.py
├── templates/
│   ├── index.html        # Operations Center paneli
│   ├── login.html        # Giriş / kayıt sayfası
│   └── report.html       # Yazdırılabilir (PDF) rapor
├── static/
│   ├── css/style.css     # Arayüz stilleri (aydınlık + karanlık tema)
│   └── js/               # app.js, login.js, theme.js, report.js
├── tests/
│   ├── test_engine.py    # Tarayıcı ve risk motoru testleri
│   ├── test_plugins.py   # Eklenti testleri
│   ├── test_api.py       # API ve veritabanı testleri
│   ├── test_auth.py      # Giriş, oturum, OAuth testleri
│   └── test_insights.py  # İstatistik ve karşılaştırma testleri
├── deploy/Caddyfile      # HTTPS ters vekil ayarı
├── Dockerfile, docker-compose.yml
├── .env.example          # Tüm ayarlar (kopyalayıp .env yapın)
├── data/                 # reconclaw_v4.db (otomatik oluşturulur)
├── plugins               # Etkin eklentiler listesi
├── requirements.txt
└── README.md
```

---

## 💾 Veritabanı

Uygulama ilk açılışta `data/reconclaw_v4.db` dosyasını ve tabloları otomatik oluşturur. Farklı bir konum için `RECONCLAW_DB` ortam değişkenini kullanabilirsiniz.

| Tablo        | Alanlar                                                                          |
| ------------ | -------------------------------------------------------------------------------- |
| `scans`      | `id`, `target`, `ip_address`, `open_count`, `risk_score`, `risk_level`, `duration`, `scan_time`, `report` (tam JSON rapor) |
| `open_ports` | `id`, `scan_id`, `port`, `protocol`, `service`, `banner`, `risk`                 |
| `findings`   | `id`, `scan_id`, `plugin`, `port`, `severity`, `title`, `detail`                 |
| `users`      | `id`, `email`, `name`, `password_hash` (scrypt), `avatar_url`, `api_token` (SHA-256), `created_at`, `last_login` |
| `identities` | `id`, `user_id`, `provider` (google/github/…), `subject`                          |
| `sessions`   | `token_hash`, `user_id`, `created_at`, `expires_at`, `user_agent`                |
| `oauth_states` | `state`, `provider`, `verifier`, `created_at` (10 dk geçerli, tek kullanımlık) |

`scans` tablosuna v5.0'da `user_id` sütunu eklenmiştir; eski veritabanları açılışta otomatik güncellenir.

---

## 🧪 Testler

```bash
pip install pytest httpx
pytest
```

---

## 🛣️ Yol Haritası

**✅ v1.0 – v3.0**
- İlk TCP tarayıcı, JSON çıktısı, CLI
- Koyu tema, servis tanımlama, performans iyileştirmeleri
- Dashboard, FastAPI, SQLite, risk motoru, canlı terminal

**🚀 v4.0 Phantom**
- [x] Modüler mimari (`core/`, `templates/`, `static/`)
- [x] Asenkron, eşzamanlılık sınırlı tarama motoru
- [x] Banner grabbing & sürüm tespiti
- [x] CVE imza uyarı sistemi ve öneri motoru
- [x] Tarama geçmişi, geçmiş rapor görüntüleme ve JSON dışa aktarma
- [x] Eklenti sistemi (HTTP güvenlik başlıkları, TLS sertifika analizi)

**🌌 v5.0 Nebula** *(mevcut sürüm)*
- [x] Operations Center paneli (istatistik kartları, olay akışı, trend ve port grafikleri)
- [x] Aydınlık / karanlık tema
- [x] E-posta + Google / GitHub / Microsoft / Apple ile giriş, kullanıcıya özel geçmiş
- [x] Tarama karşılaştırma, ağ haritası, PDF / CSV rapor
- [x] API anahtarı, hız sınırı, güvenlik başlıkları
- [x] Docker + Caddy ile alan adında otomatik HTTPS

**🔭 Sonraki adımlar**
- [ ] UDP tarama
- [ ] Zamanlanmış (periyodik) taramalar ve e-posta bildirimi
- [ ] İki adımlı doğrulama (TOTP)

**🌠 v6.0**
- [ ] Yapay zekâ destekli pentest asistanı
- [ ] Makine öğrenmesi ile anomali tespiti
- [ ] Bulut tarama (AWS, Azure, Kubernetes)
- [ ] SIEM entegrasyonu & sürekli izleme
- [ ] MITRE ATT&CK eşleştirme, OWASP / ISO 27001 uyumluluk raporları

---

## ⚖️ Yasal Uyarı

ReconClaw yalnızca **sahibi olduğunuz** veya **yazılı izin aldığınız** sistemlerde, **eğitim** ve **etik güvenlik testi** amacıyla kullanılmalıdır. İzinsiz port taraması birçok ülkede (Türkiye'de TCK 243–245 kapsamında) suç teşkil edebilir. Yazılımın kötüye kullanımından doğan tüm hukuki sorumluluk kullanıcıya aittir.

---

## ✍️ Geliştirici

<p align="center">
<b>Burak Özdemir</b> — <a href="https://github.com/Pireburak">@Pireburak</a><br>
<sub>ReconClaw'ı beğendiyseniz ⭐ vermeyi unutmayın!</sub>
</p>
