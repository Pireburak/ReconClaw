# 🦅 ReconClaw v4.0 Ultimate

### *AI Destekli Ağ Keşfi ve Güvenlik Analiz Platformu*

<p align="center">

![Version](https://img.shields.io/badge/Version-v3.0%20Ultimate-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge\&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge\&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge\&logo=sqlite)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge)

</p>

---

# 🚀 ReconClaw Nedir?

ReconClaw; yetkili ağ keşfi (Reconnaissance), port analizi, servis tespiti ve güvenlik değerlendirmesi amacıyla geliştirilen modern bir siber güvenlik platformudur.

Sistem yalnızca açık portları listelemek yerine;

* Servis analizi yapar
* Risk puanı hesaplar
* DNS çözümlemesi gerçekleştirir
* Sonuçları JSON olarak raporlar
* Taramaları SQLite veritabanına kaydeder
* Web Dashboard üzerinden canlı olarak gösterir

---

# 📊 Risk Analiz Modeli

```````markdown
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
3306    MySQL

───────────────────────────────────────────────────────

Toplam Risk Skoru  : 78 / 100

Risk Seviyesi      : 🔴 Kritik Risk

───────────────────────────────────────────────────────

AI Security Recommendation

✔ Gereksiz servisleri devre dışı bırakın.
✔ Güvenlik duvarı kurallarını güncelleyin.
✔ Servis sürümlerini güncel tutun.
✔ Güçlü parola ve MFA kullanın.
✔ Düzenli güvenlik taraması gerçekleştirin.

═══════════════════════════════════════════════════════
```

### 🧠 Risk Hesaplama Kriterleri

- 🔹 Açık port sayısı
- 🔹 Servis türü
- 🔹 Servisin kritikliği
- 🔹 Olası saldırı yüzeyi
- 🔹 Bilinen güvenlik riskleri
- 🔹 Güvenlik yapılandırması
- 🔹 Gelecekte CVE ve MITRE ATT&CK analiz desteği

> **Not:** Risk puanı yalnızca ön değerlendirme amacıyla hesaplanır. Kesin güvenlik analizi yerine sistem yöneticilerine hızlı karar desteği sunmayı hedefler.

---
````

              
```

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
        ┌────────┼────────┐
        ▼        ▼        ▼
   DNS Resolver Risk AI SQLite
        │
        ▼
     ⚡ Core Scanner
        │
        ▼
    TCP / Socket Engine
```

---

# ⚡ Temel Özellikler

| Özellik       | Durum |
| ------------- | ----- |
| TCP Port Scan | ✅     |
| DNS Resolver  | ✅     |
| Risk Engine   | ✅     |
| FastAPI       | ✅     |
| SQLite        | ✅     |
| Dashboard     | ✅     |
| JSON Export   | ✅     |
| CLI           | ✅     |
| AI Brain      | ✅     |
| Responsive UI | ✅     |

---

# 🧠 AI Brain

AI Brain modülü;

* Risk puanı üretir
* Servisleri sınıflandırır
* Portları analiz eder
* Kritik servisleri önceliklendirir
* Dashboard verisini hazırlar
* JSON çıktısını oluşturur

---

# ⚡ Core Engine

Core Engine;

* TCP Socket kullanır
* Hızlı timeout uygular
* Çok düşük RAM tüketir
* Asenkron mimariye hazırdır
* JSON raporu üretir

---

# 📂 Proje Yapısı

```text
ReconClaw/

├── ai-brain/
├── core/
├── static/
├── templates/
├── reports/
├── database/
├── assets/
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

## ✅ v1.0

* İlk TCP Scanner
* JSON Çıktısı
* CLI

---

## ✅ v2.0

* Dark Theme
* Servis Tanımlama
* Performans İyileştirmesi

---

## ✅ v3.0

* AI Brain
* Dashboard
* FastAPI
* SQLite
* Risk Motoru
* Canlı Terminal

---

## 🚀 v4.0

* UDP Scan
* Banner Grabbing
* Version Detection
* SSL Analizi
* CVE Database
* MITRE ATT&CK
* GeoIP
* Whois
* ASN Lookup
* PDF Rapor
* HTML Export
* Docker
* JWT Authentication
* Plugin Sistemi

---

## 🌌 v5.0

* AI Pentest Assistant
* Machine Learning
* Cloud Scanner
* AWS
* Azure
* Kubernetes
* SIEM Integration
* Continuous Monitoring
* Attack Surface Management
* Threat Intelligence
* Compliance Engine
* OWASP Top 10
* ISO 27001
* NIST
* Plugin Marketplace

---

# 🖼️ Dashboard Önizleme

```text
┌─────────────────────────────────────┐
│ TARGET : example.com                │
│ STATUS : SCANNING...                │
│ OPEN PORTS : 7                      │
│ RISK SCORE : 78/100                 │
│ ████████████████████████            │
└─────────────────────────────────────┘
```

---

# 💾 Veritabanı

| Tablo        | Açıklama       |
| ------------ | -------------- |
| scan_history | Tarama geçmişi |
| target       | Hedef          |
| open_ports   | Açık portlar   |
| risk_score   | Risk puanı     |
| scan_time    | Tarama zamanı  |

---

# ⚖️ Yasal Uyarı

ReconClaw yalnızca **yetkili**, **izinli** ve **etik** güvenlik testleri amacıyla geliştirilmiştir.

Herhangi bir kurum, kuruluş, sunucu veya kişiye ait sistemlerin yazılı izin olmaksızın taranması; bulunduğunuz ülkenin bilişim suçları, kişisel verilerin korunması ve elektronik haberleşme mevzuatlarına aykırılık oluşturabilir.

Bu yazılım savunma odaklı geliştirilmiştir. Geliştirici; yazılımın kötü niyetli kullanımı, yetkisiz ağ taramaları, veri ihlalleri, hizmet kesintileri veya oluşabilecek hukuki sonuçlardan sorumlu değildir.

Yazılımı kullanan herkes, gerçekleştirdiği tüm işlemlerin hukuki sorumluluğunu kabul etmiş sayılır.

---

# ✍️ Geliştirici

```text
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝

Engineered with ☕ by

Pireburak

ReconClaw Framework

© 2026
Tüm Hakları Saklıdır.
```
