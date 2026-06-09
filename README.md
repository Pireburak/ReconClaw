# 🦅 ReconClaw V1.0 - Otonom Keşif ve Zafiyet Tarama Sistemi

ReconClaw, modern mikroservis mimarisi kullanılarak sıfırdan geliştirilmiş, yüksek performanslı ve otonom bir siber güvenlik (Pentest) aracıdır. Sistem; dış dünyayla iletişimi ve veritabanı yönetimini sağlayan **Python (FastAPI)** tabanlı bir "Beyin" ile, saniyeler içinde binlerce porta eşzamanlı saldırı yapabilen **Rust (Tokio)** tabanlı bir "Kas Gücünden" oluşmaktadır.

## 🚀 Öne Çıkan Özellikler

* **Asenkron Tarama Motoru:** Rust ve `tokio` kütüphanesi sayesinde, hedeflenen portlar sırayla değil, asenkron (eşzamanlı) olarak taranır. Bu sayede Nmap hızında performans elde edilir.
* **Akıllı Radar (DNS Çözümleme):** Hedef olarak sadece IP adresi değil, `scanme.nmap.org` gibi alan adları (domain) girilebilir. Sistem, hedefin gerçek IP adresini arka planda otonom olarak çözer.
* **Merkezi Kontrol Paneli:** Kaba saba komut satırları yerine; taramaların başlatılabileceği, sonuçların ve portların anlık izlenebileceği şık, HTML/JS tabanlı bir siber güvenlik arayüzü sunar.
* **Kalıcı Hafıza (SQLite):** Yapılan her tarama, tarihi, hedefi ve bulunan açık portlarıyla birlikte sistemin dahili veritabanına kaydedilir. `/api/history` rotası ile geçmişe dönük analiz yapılabilir.
* **Mikroservis Mimarisi:** Frontend, Backend ve Core-Engine birbirlerinden tamamen bağımsız ancak kusursuz bir uyum içinde çalışır.

## 🛠️ Kullanılan Teknolojiler

**AI-Brain (Sinir Sistemi):**
* Python 3.x
* FastAPI & Uvicorn
* SQLite (Veritabanı)

**Core-Engine (Kas Gücü):**
* Rust
* Tokio (Asenkron işlemler)
* Serde & Clap (JSON ayrıştırma ve Argüman yönetimi)

## ⚙️ Kurulum ve Çalıştırma

Sistemi Kali Linux veya herhangi bir Linux dağıtımında çalıştırmak için:

1. Depoyu klonlayın:
```bash
git clone [https://github.com/Pireburak/ReconClaw.git](https://github.com/Pireburak/ReconClaw.git)
cd ReconClaw
