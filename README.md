# 🦅 ReconClaw V1.0 - Otonom Keşif ve Zafiyet Tarama Sistemi

ReconClaw, modern mikroservis mimarisi kullanılarak sıfırdan geliştirilmiş, yüksek performanslı ve otonom bir siber güvenlik (Pentest) aracıdır. Bu proje, ağ keşfi ve port tarama süreçlerini otomatize etmek, hızlandırmak ve sonuçları kalıcı olarak kayıt altına almak amacıyla tasarlanmıştır.

Sistem iki ana omurgadan oluşur: Dış dünyayla iletişimi ve veritabanı yönetimini sağlayan **Python (FastAPI)** tabanlı bir "Sinir Sistemi" ve saniyeler içinde binlerce porta eşzamanlı saldırı yapabilen **Rust (Tokio)** tabanlı bir "Kas Gücü".

---

## 🚀 Öne Çıkan Özellikler

* **⚡ Asenkron Tarama Motoru:** Rust ve `tokio` kütüphanesi sayesinde, hedeflenen portlar sırayla değil, asenkron (eşzamanlı) olarak taranır. Geleneksel tarayıcılara göre muazzam bir hız artışı sağlar.
* **🎯 Akıllı Radar (DNS Çözümleme):** Hedef olarak sadece IP adresi değil, `scanme.nmap.org` gibi alan adları (domain) girilebilir. Python motoru, hedefin gerçek IP adresini OSINT teknikleriyle arka planda otonom olarak çözer.
* **🖥️ Merkezi Kontrol Paneli (UI):** Kaba saba komut satırları yerine; taramaların başlatılabileceği, sonuçların ve portların anlık izlenebileceği siyah/neon-yeşil temalı HTML/JS tabanlı bir siber güvenlik arayüzü sunar.
* **🧠 Kalıcı Hafıza (SQLite):** Yapılan her tarama; tarihi, hedefi (Domain + IP) ve bulunan açık portlarıyla birlikte sistemin dahili veritabanına otomatik kaydedilir.
* **🧩 Mikroservis Mimarisi:** Frontend, Backend ve Core-Engine birbirlerinden izole edilmiş, kendi içlerinde bağımsız ancak API'ler aracılığıyla kusursuz bir uyum içinde çalışır.

---

## 🛠️ Sistem Mimarisi ve Teknoloji Yığını

**AI-Brain (Yönetim ve İletişim Katmanı):**
* **Dil:** Python 3.x
* **Framework:** FastAPI & Uvicorn (Yüksek performanslı asenkron web sunucusu)
* **Veritabanı:** SQLite3 (Lokal ve hafif veri depolama)
* **Ağ İşlemleri:** Yerleşik `socket` kütüphanesi (DNS çözümleme)

**Core-Engine (Tarama ve Analiz Katmanı):**
* **Dil:** Rust
* **Eşzamanlılık:** Tokio (Asenkron runtime)
* **Veri İşleme:** Serde & Serde_json (JSON serileştirme)
* **CLI Yönetimi:** Clap (Argüman ayrıştırma)

---

## 📡 API Uç Noktaları (Endpoints)

ReconClaw'un sinir sistemi, dış modüllerin entegre olabilmesi için aşağıdaki RESTful API yapısını kullanır:

* `GET /` : Merkezi HTML kontrol panelini (Arayüzü) render eder.
* `POST /api/scan` : Hedef IP/Domain ve port limitini JSON olarak alır, Rust motorunu tetikler ve tarama sonucunu veritabanına yazarak döndürür.
* `GET /api/history` : SQLite veritabanındaki en son yapılan 10 taramanın detaylı geçmişini JSON formatında listeler.

---

## ⚙️ Kurulum ve Çalıştırma Rehberi

Sistemi Kali Linux veya herhangi bir Debian tabanlı Linux dağıtımında çalıştırmak için aşağıdaki adımları sırasıyla uygulayın:

**1. Depoyu Klonlayın:**
```bash
git clone [https://github.com/Pireburak/ReconClaw.git](https://github.com/Pireburak/ReconClaw.git)
cd ReconClaw
