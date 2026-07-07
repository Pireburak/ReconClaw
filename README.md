# 🦅 ReconClaw v4.0 Ultimate

### *AI Destekli Ağ Keşfi ve Güvenlik Analiz Platformu*

<p align="center">
<img src="[https://img.shields.io/badge/Version-v4.0%20Ultimate-success?style=for-the-badge](https://img.shields.io/badge/Version-v4.0%20Ultimate-success?style=for-the-badge)" alt="Version">
<img src="[https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)" alt="Python">
<img src="[https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi](https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi)" alt="FastAPI">
<img src="[https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)" alt="SQLite">
<img src="[https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)" alt="Status">
<img src="[https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge](https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge)" alt="License">
</p>

---

# 🚀 ReconClaw Nedir?

ReconClaw; yetkili ağ keşfi (Reconnaissance), port analizi, servis tespiti ve güvenlik değerlendirmesi amacıyla geliştirilen modern bir siber güvenlik platformudur.

Sistem yalnızca açık portları listelemek yerine;

* Servis analizi yapar ve versiyonları çeker (Banner Grabbing)
* Risk puanı hesaplar ve AI destekli uyarılar verir
* DNS çözümlemesi gerçekleştirir
* Sonuçları JSON olarak raporlar
* Taramaları otomatik olarak yerleşik SQLite veritabanına kaydeder
* Asenkron (çok yüksek hızlı) TCP soket motoru kullanır
* Web Dashboard üzerinden canlı olarak gösterir

---

# 📊 Risk Değerlendirme Modeli

ReconClaw, gerçekleştirilen her tarama sonucunda yalnızca açık portları listelemekle kalmaz; aynı zamanda çalışan servisleri analiz ederek hedef sistem için dinamik bir **Risk Skoru** oluşturur. Bu skor, servislerin kritiklik seviyesine, olası saldırı yüzeyine ve güvenlik etkilerine göre hesaplanır.

## 🎯 Risk Seviyeleri

| Risk Seviyesi | Zafiyet Oranı | Durum | Açıklama |
|:--------------|:-------------:|:-----:|----------|
| 🟢 Düşük Risk | **0% - 25%** | Güvenli | Kritik seviyede herhangi bir güvenlik riski bulunmamaktadır. |
| 🟡 Orta Risk | **26% - 50%** | İzlenmeli | Yapılandırma iyileştirmeleri önerilir. Düzenli güvenlik kontrolleri yapılmalıdır. |
| 🟠 Yüksek Risk | **51% - 75%** | Riskli | Açık servisler saldırı yüzeyini artırmaktadır. Güvenlik önlemleri güçlendirilmelidir. |
| 🔴 Kritik Risk | **76% - 100%** | Kritik | Kritik servisler veya yüksek öneme sahip zafiyetler tespit edilmiştir. Acil aksiyon alınması önerilir. |

---

## 📌 Örnek Risk Analizi

```text
═══════════════════════════════════════════════════════

Target             : example.com
Resolved IP        : 192.168.1.10

───────────────────────────────────────────────────────
Open Ports

22      SSH
80      HTTP
443     HTTPS
3306    MySQL (Dışa Açık)
───────────────────────────────────────────────────────

Toplam Risk Skoru  : 78 / 100
Risk Seviyesi      : 🔴 Kritik Risk

───────────────────────────────────────────────────────
AI Security Recommendation

✔ [CVE-2016-10009] OpenSSH sürümünüz eski, RCE riski var.
✔ 3306 (MySQL) portunu dış ağa kapatın, IP filtrelemesi uygulayın.
✔ Gereksiz servisleri devre dışı bırakın.
✔ Güvenlik duvarı kurallarını güncelleyin.
✔ Düzenli güvenlik taraması gerçekleştirin.

═══════════════════════════════════════════════════════
```

### 🧠 Risk Hesaplama Kriterleri

- 🔹 Açık port sayısı
- 🔹 Servis türü ve versiyonu
- 🔹 Servisin kritikliği (RDP, Veritabanı vb.)
- 🔹 Olası saldırı yüzeyi
- 🔹 Bilinen güvenlik riskleri (CVE Kontrolü)
- 🔹 Güvenlik yapılandırması
- 🔹 Gelecekte MITRE ATT&CK analiz desteği

> **Not:** Risk puanı yalnızca ön değerlendirme amacıyla hesaplanır. Kesin güvenlik analizi yerine sistem yöneticilerine hızlı karar desteği sunmayı hedefler.
> Ortalama örnek risk seviyesi (%78)

---

# 🏗️ Sistem Mimarisi

```text
           🌐 Web Dashboard
                   │
                   ▼
            FastAPI REST API
                   │
                   ▼
             🧠 AI Brain
       ┌───────────┼───────────┐
       ▼           ▼           ▼
  DNS Resolver  Risk AI     SQLite
       │
       ▼
    ⚡ Core Scanner (v4.0)
       │
       ▼
  Async TCP / Socket Engine
```

---

# ⚡ Temel Özellikler

| Özellik        | Durum | Özellik           | Durum |
| -------------- | ----- | ----------------- | ----- |
| TCP Port Scan  | ✅     | Dashboard         | ✅     |
| DNS Resolver   | ✅     | JSON Export       | ✅     |
| Risk Engine    | ✅     | CLI               | ✅     |
| FastAPI        | ✅     | AI Brain          | ✅     |
| SQLite         | ✅     | Version Detection | ✅     |

---

# 📂 Proje Yapısı

*v4.0 ile birlikte proje karmaşık klasörlerden kurtulmuş ve "Tek Dosya Mimarisi"ne geçmiştir.*

```text
ReconClaw/

├── main.py            (Tüm sistemin kalbi)
├── reconclaw.db       (Otomatik oluşturulur)
├── README.md
└── requirements.txt
```

---

# 📈 Geliştirme Durumu

```text
v1.0  ████████████████████ 100%
v2.0  ████████████████████ 100%
v3.0  ████████████████████ 100%
v4.0  ███████████░░░░░░░░░ 55%
v5.0  █████░░░░░░░░░░░░░░░ 20%
```

---

# 🛣️ Yol Haritası

## ✅ v1.0 - v3.0
* İlk TCP Scanner, JSON Çıktısı, CLI
* Dark Theme, Servis Tanımlama, Performans İyileştirmesi
* AI Brain, Dashboard, FastAPI, SQLite, Risk Motoru, Canlı Terminal

## 🚀 v4.0
* Tek Dosya Mimarisi (Klasörsüz kolay kullanım)
* Asenkron (Yüksek Hızlı) Tarama Motoru
* Banner Grabbing & Version Detection
* AI Destekli CVE Uyarı Sistemi
* UDP Scan (Planlanıyor)
* SSL Analizi (Planlanıyor)
* JWT Authentication & Docker (Planlanıyor)

## 🌌 v5.0
* AI Pentest Assistant
* Machine Learning
* Cloud Scanner (AWS, Azure, Kubernetes)
* SIEM Integration & Continuous Monitoring
* Threat Intelligence & Compliance Engine (OWASP, ISO 27001)

---

# 🖼️ Dashboard Önizleme

```text
┌─────────────────────────────────────┐
│ TARGET : example.com                │
│ STATUS : SCANNING...                │
│ OPEN PORTS : 7                      │
│ RISK SCORE : 78/100                 │
│ ████████████
