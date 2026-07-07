# 🦅 ReconClaw v4.0 Ultimate

### *AI Destekli Ağ Keşfi ve Güvenlik Analiz Platformu*

<p align="center">

![Version](https://img.shields.io/badge/Version-v4.0%20Ultimate-success?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-blueviolet?style=for-the-badge)

</p>

---

# 🚀 ReconClaw Nedir?

ReconClaw; yetkili ağ keşfi (Reconnaissance), port analizi, servis tespiti ve güvenlik değerlendirmesi amacıyla geliştirilen modern bir siber güvenlik platformudur.

Sistem yalnızca açık portları listelemek yerine;

* **[v4.0]** TCP ve UDP servis analizi yapar
* **[v4.0]** Banner Grabbing ve Versiyon tespiti yapar
* **[v4.0]** SSL/TLS sertifika analizi gerçekleştirir
* Risk puanı hesaplar ve MITRE ATT&CK eşleştirmesi sunar
* DNS çözümlemesi ve GeoIP/Whois OSINT verisi toplar
* Sonuçları JSON, HTML ve PDF olarak raporlar
* Taramaları SQLite veritabanına kaydeder
* JWT Korumalı Web Dashboard üzerinden canlı olarak gösterir

---

# 📊 Risk Analiz Modeli

ReconClaw, gerçekleştirilen her tarama sonucunda yalnızca açık portları listelemekle kalmaz; aynı zamanda çalışan servisleri analiz ederek hedef sistem için dinamik bir **Risk Skoru** oluşturur. Bu skor, servislerin kritiklik seviyesine, olası saldırı yüzeyine ve güvenlik etkilerine göre hesaplanır.

## 🎯 Risk Seviyeleri

| Risk Seviyesi | Zafiyet Oranı | Durum | Açıklama |
|:--------------|:-------------:|:-----:|----------|
| 🟢 Düşük Risk | **0% - 25%** | Güvenli | Kritik seviyede herhangi bir güvenlik riski bulunmamaktadır. |
| 🟡 Orta Risk | **26% - 50%** | İzlenmeli | Yapılandırma iyileştirmeleri önerilir. Düzenli güvenlik kontrolleri yapılmalıdır. |
| 🟠 Yüksek Risk | **51% - 75%** | Riskli | Açık servisler saldırı yüzeyini artırmaktadır. Güvenlik önlemleri güçlendirilmelidir. |
| 🔴 Kritik Risk | **76% - 100%** | Kritik | Kritik servisler, eski versiyonlar (CVE) veya yüksek öneme sahip zafiyetler tespit edilmiştir. Acil aksiyon alınması önerilir. |

---

## 📌 Örnek Risk Analizi

```text
═══════════════════════════════════════════════════════

Target             : example.com
Resolved IP        : 192.168.1.10
Location           : Frankfurt, DE (AS16509)

───────────────────────────────────────────────────────

Open Ports & Services

22      SSH      OpenSSH 7.2p2 (⚠️ Eski Sürüm)
80      HTTP     nginx 1.18.0
443     HTTPS    nginx 1.18.0 (❌ SSL: TLS 1.0)
3306    MySQL    MariaDB 10.3 (🔴 Dışa Açık)

───────────────────────────────────────────────────────

Toplam Risk Skoru  : 78 / 100

Risk Seviyesi      : 🔴 Kritik Risk

───────────────────────────────────────────────────────

AI Security Recommendation & MITRE ATT&CK

✔ [CVE-2016-10009] OpenSSH sürümünüz eski, RCE riski var.
✔ [T1190] 3306 (MySQL) portunu dış ağa kapatın.
✔ [T1562] TLS 1.0 protokolünü devre dışı bırakıp TLS 1.2+ geçin.
✔ Gereksiz servisleri devre dışı bırakın.
✔ Düzenli güvenlik taraması gerçekleştirin.

═══════════════════════════════════════════════════════
