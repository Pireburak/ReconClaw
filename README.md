<h1 align="center">🦅 ReconClaw v4.0 Phantom</h1>

<p align="center"><b>Asenkron Ağ Keşfi, Port Tarama ve Risk Analiz Platformu</b></p>

<p align="center">
<img src="https://img.shields.io/badge/Version-v4.0%20Phantom-success?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
<img src="https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge" alt="License">
</p>

<p align="center">
<a href="#-kurulum">Kurulum</a> •
<a href="#-kullanım">Kullanım</a> •
<a href="#-api">API</a> •
<a href="#-risk-değerlendirme-modeli">Risk Modeli</a> •
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
- 🖥️ Sonuçları canlı terminal görünümlü **web dashboard** üzerinde sunar

---

## ⚡ Özellikler

| Özellik                        | Durum | Özellik                     | Durum |
| ------------------------------ | :---: | --------------------------- | :---: |
| Asenkron TCP Connect Tarama    |  ✅   | Web Dashboard (responsive)  |  ✅   |
| DNS Çözümleme                  |  ✅   | REST API (JSON)             |  ✅   |
| Banner Grabbing / Sürüm Tespiti|  ✅   | Tarama Geçmişi (SQLite)     |  ✅   |
| Kural Tabanlı Risk Motoru      |  ✅   | CVE İmza Eşleştirme         |  ✅   |
| Yaygın Port / Aralık Taraması  |  ✅   | Otomatik Testler (pytest)   |  ✅   |
| UDP Tarama                     |  🔜   | SSL/TLS Analizi             |  🔜   |

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

1. Hedef IP adresini veya alan adını girin (`https://site.com/yol` gibi girdiler otomatik temizlenir).
2. Port kapsamını seçin:
   - **Yaygın portlar** → güvenlik açısından kritik 27 port (FTP, SSH, SMB, RDP, veritabanları…)
   - **1 → Maks. port** → belirttiğiniz sınıra kadar tüm portlar (en fazla 65535)
3. **TARAMAYI BAŞLAT** butonuna basın; sonuçlar, CVE uyarıları ve öneriler anında ekrana gelir.

> 💡 Yasal ve güvenli test için Nmap'in resmi test sunucusu `scanme.nmap.org` kullanılabilir.

---

## 🔌 API

Etkileşimli API dokümantasyonu: **http://127.0.0.1:8000/docs**

### `POST /api/scan`

```bash
curl -X POST http://127.0.0.1:8000/api/scan \
     -H "Content-Type: application/json" \
     -d '{"target": "scanme.nmap.org"}'
```

| Alan       | Tip    | Zorunlu | Açıklama                                                     |
| ---------- | ------ | :-----: | ------------------------------------------------------------ |
| `target`   | string |   ✅    | IP adresi veya alan adı                                      |
| `max_port` | int    |   —     | Verilirse `1..max_port` taranır, verilmezse yaygın portlar   |
| `timeout`  | float  |   —     | Port başına bağlantı zaman aşımı (0.2 – 5 sn, varsayılan 1) |

<details>
<summary>Örnek yanıt</summary>

```json
{
  "success": true,
  "scan_id": 12,
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
  "analysis": [
    { "port": 22, "protocol": "TCP", "banner": "SSH-2.0-OpenSSH_5.3", "service": "SSH", "risk": 80 }
  ]
}
```
</details>

### `GET /api/history?limit=20`

Son taramaları en yeniden eskiye doğru döndürür.

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

## 🏗️ Sistem Mimarisi

```text
        🌐 Web Dashboard (templates + static)
                     │  fetch /api/scan
                     ▼
            ⚙️  FastAPI (main.py)
                     │
        ┌────────────┼──────────────┐
        ▼            ▼              ▼
  AsyncScanner   RiskAnalyzer   db_manager
  (DNS + TCP +   (skor, CVE,    (SQLite:
   banner)        öneriler)      geçmiş)
        └──────── core/engine.py ───┘
```

---

## 📂 Proje Yapısı

```text
ReconClaw/
├── main.py               # FastAPI uygulaması ve API uç noktaları
├── core/
│   ├── engine.py         # AsyncScanner + RiskAnalyzer
│   └── db_manager.py     # SQLite bağlantısı, tablolar, kayıt işlemleri
├── templates/
│   └── index.html        # Dashboard şablonu
├── static/
│   ├── css/style.css     # Arayüz stilleri
│   └── js/app.js         # Arayüz mantığı
├── tests/
│   └── test_engine.py    # Birim testleri
├── data/                 # reconclaw_v4.db (otomatik oluşturulur)
├── requirements.txt
└── README.md
```

---

## 💾 Veritabanı

Uygulama ilk açılışta `data/reconclaw_v4.db` dosyasını ve tabloları otomatik oluşturur. Farklı bir konum için `RECONCLAW_DB` ortam değişkenini kullanabilirsiniz.

| Tablo        | Alanlar                                                                          |
| ------------ | -------------------------------------------------------------------------------- |
| `scans`      | `id`, `target`, `ip_address`, `open_count`, `risk_score`, `risk_level`, `duration`, `scan_time` |
| `open_ports` | `id`, `scan_id`, `port`, `protocol`, `service`, `banner`, `risk`                 |

---

## 🧪 Testler

```bash
pip install pytest
pytest
```

---

## 🛣️ Yol Haritası

**✅ v1.0 – v3.0**
- İlk TCP tarayıcı, JSON çıktısı, CLI
- Koyu tema, servis tanımlama, performans iyileştirmeleri
- Dashboard, FastAPI, SQLite, risk motoru, canlı terminal

**🚀 v4.0 Phantom** *(mevcut sürüm)*
- [x] Modüler mimari (`core/`, `templates/`, `static/`)
- [x] Asenkron, eşzamanlılık sınırlı tarama motoru
- [x] Banner grabbing & sürüm tespiti
- [x] CVE imza uyarı sistemi ve öneri motoru
- [x] Tarama geçmişi
- [ ] UDP tarama
- [ ] SSL/TLS analizi
- [ ] JWT kimlik doğrulama & Docker desteği

**🌌 v5.0**
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
