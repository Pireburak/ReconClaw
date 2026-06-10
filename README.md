# 🦅 ReconClaw V2.0 | Otonom Zafiyet & Asenkron Port Tarama Motoru

<p align="center">
  <img src="https://img.shields.io/badge/Rust-ASYNCHRONOUS_CORE-orange?style=for-the-badge&logo=rust" alt="Rust">
  <img src="https://img.shields.io/badge/Python-API_GATEWAY-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/C-MEMORY_OPTIMIZED-lightgrey?style=for-the-badge&logo=c" alt="C">
  <img src="https://img.shields.io/badge/JavaScript-UI_REACTIVE-yellow?style=for-the-badge&logo=javascript" alt="JS">
</p>

ReconClaw, hedef ağlar üzerinde milisaniyeler seviyesinde port keşfi, servis tespiti ve otonom DNS çözünürlüğü yapabilen yeni nesil bir siber güvenlik aracıdır. Geleneksel tarama betiklerinin aksine ReconClaw, gücünü modern asenkron algoritmalardan ve mikroservis mimarisinden alır.

---

## 🛠️ Teknik Yetkinlik & Teknoloji Puanlaması
*Proje kapsamında kullanılan teknolojilerin derinliği ve sistem üzerindeki ağırlığı:*

- **🦀 Rust (Core Engine):** %45 | *Yüksek performanslı ağ paketleme ve Non-blocking I/O işlemleri.*
- **🐍 Python (API Gateway):** %30 | *FastAPI tabanlı güvenli veri akışı ve istek yönetimi.*
- **📜 C (Memory/Low-level):** %15 | *Sistem kaynak yönetimi ve düşük seviyeli ağ optimizasyonları.*
- **⚡ JavaScript (UI/UX):** %10 | *Neon tasarımlı reaktif arayüz ve raporlama modülü.*

---

## 🧠 Algoritmik Çekirdek & Mimari Tasarım

### 1. Asenkron Tarama Algoritması (Rust & Tokio Motoru)
ReconClaw V2.0, **Non-Blocking I/O** algoritmasını kullanır:
*   **Green Threading:** Tokio çalışma zamanı ile binlerce port sorgusu, işletim sistemini yormadan hafif iş parçacıklarına bölünür.
*   **Event Loop:** SYN paket cevapları asenkron dinlenir; zaman aşımına uğrayan paketler anında `drop` edilir, böylece ağ üzerinde gereksiz trafik oluşmaz.

### 2. API Gateway & İstemci İletişimi (FastAPI)
Rust motorunun ham verileri, Python tabanlı FastAPI katmanına iletilir. 
*   Burası sistemin beyni (ai-brain) olarak çalışır; gelen istekleri doğrular, hatalı hedefleri filtreler ve sonuçları standardize ederek ön yüze asenkron olarak basar.

---

## 🚀 V2.0 Öne Çıkan Özellikler
*   **⚡ Otonom Asenkron Tarama:** Dinamik hız ayarı.
*   **🌐 Reaktif Neon Arayüz:** Hedef kilitlenme animasyonları ve canlı terminal imleci.
*   **📊 Kurumsal Raporlama:** Tek tıkla CSV/Excel dışa aktarım modülü.
*   **🛡️ Güvenli Mikroservis:** İzole edilmiş ve güvenli veri akışı.

---

## 🛠️ Kurulum & Ateşleme

```bash
git clone [https://github.com/Pireburak/ReconClaw.git](https://github.com/Pireburak/ReconClaw.git)
cd ReconClaw/ai-brain
pip install fastapi uvicorn
uvicorn main:app --reload
