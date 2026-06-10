# 🦅 ReconClaw V2.0 | Otonom Zafiyet & Asenkron Port Tarama Motoru

![Version](https://img.shields.io/badge/Version-2.0.1-brightgreen?style=for-the-badge)
![Architecture](https://img.shields.io/badge/Architecture-Microservices-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/API_Gateway-FastAPI-blue?style=for-the-badge&logo=python)
![Rust](https://img.shields.io/badge/Core_Engine-Rust_Tokio-orange?style=for-the-badge&logo=rust)
![Frontend](https://img.shields.io/badge/UI%2FUX-Neon_Design-ff69b4?style=for-the-badge)

ReconClaw, hedef ağlar ve sistemler üzerinde milisaniyeler seviyesinde port keşfi, servis tespiti ve otonom DNS çözünürlüğü yapabilen yeni nesil bir siber güvenlik aracıdır. Geleneksel ardışık (sequential) tarama betiklerinin aksine ReconClaw, gücünü modern asenkron algoritmalardan ve mikroservis mimarisinden alır. 

Son kullanıcıya hitap eden reaktif web arayüzü sayesinde, operasyonel süreçleri terminal ekranından çıkarıp profesyonel bir kontrol paneline taşır.

---

## 🧠 Algoritmik Çekirdek & Mimari Tasarım

ReconClaw'un kalbinde, kaynak tüketimini (CPU/RAM) optimize eden ve tarama hızını maksimize eden iki ana katman bulunur:

### 1. Asenkron Tarama Algoritması (Rust & Tokio Motoru)
Geleneksel tarayıcılar (örneğin standart Nmap betikleri) her port için TCP Three-Way Handshake (Üçlü El Sıkışma) işlemini sırayla bekler. ReconClaw V2.0 ise **Non-Blocking I/O (Engellemesiz Girdi/Çıktı)** algoritmasını kullanır:
*   **Green Threading:** Tokio çalışma zamanı (runtime) kullanılarak, aynı anda binlerce port sorgusu işletim sistemini yormadan hafif iş parçacıklarına (green threads) bölünür.
*   **Event Loop (Olay Döngüsü):** Gönderilen SYN paketlerinin cevapları asenkron olarak dinlenir. Zaman aşımına (Timeout) uğrayan veya `Connection Refused` dönen paketler anında düşürülür (drop), böylece ağ üzerinde gereksiz trafik yaratılmaz ve tespit hızı artırılır.

### 2. API Gateway & İstemci İletişimi (FastAPI)
Rust motorunun elde ettiği ham veriler, Python tabanlı FastAPI katmanına iletilir. 
*   Burası sistemin beyni (ai-brain) olarak çalışır. Gelen istekleri doğrular (Validation), hatalı hedefleri filtreler ve sonuçları JSON formatında standardize ederek ön yüze (Client) asenkron olarak basar.

---

## 🚀 V2.0 Öne Çıkan Özellikleri

*   **⚡ Otonom Asenkron Tarama:** Hedefin durumuna göre tarama hızını dinamik olarak ayarlayan Rust çekirdeği.
*   **🌐 Reaktif Arayüz (UI/UX):** Terminal zorunluluğunu bitiren, hedef kilitlenme animasyonlarına, canlı terminal imlecine ve hata yönetimine sahip neon tasarımlı kontrol paneli.
*   **📊 Kurumsal Raporlama (CSV Export):** Taraması biten hedeflerin açık port verilerini ve durum analizlerini tek tıkla kurumsal formata uygun Excel/CSV raporuna dönüştürme modülü.
*   **🛡️ Güvenli Mikroservis Yapısı:** Ön yüz (HTML/JS) ile asıl tarama motoru arasına çekilen FastAPI duvarı sayesinde izole edilmiş ve güvenli veri akışı.

---

## 🛠️ Kurulum & Sistemin Ateşlenmesi

Sistemi lokal ortamınızda (Kali Linux / Ubuntu / macOS) ayağa kaldırmak için aşağıdaki adımları izleyin:

```bash
# 1. Kaynak Kodları Klonlayın
git clone [https://github.com/Pireburak/ReconClaw.git](https://github.com/Pireburak/ReconClaw.git)
cd ReconClaw/ai-brain

# 2. Gerekli Bağımlılıkları Yükleyin (FastAPI & Uvicorn)
pip install fastapi uvicorn

# 3. API Geçidini ve Sunucuyu Başlatın
uvicorn main:app --reload
