<p align="center"><img src="static/img/banner.jpg" alt="ReconClaw — rakun maskotu" width="100%"></p>

<h1 align="center">🦝 ReconClaw v8.2 Cortex</h1>

<p align="center"><b>Asenkron Ağ Keşfi, Sürekli Saldırı Yüzeyi İzleme ve Yapay Zekâ Destekli Risk Analiz Platformu</b><br>
<i>Maskeli gözlerle keşfeder, pençesiyle açıkları yakalar.</i></p>

<p align="center">
<img src="https://img.shields.io/badge/Version-v8.2%20Cortex-E8751A?style=for-the-badge" alt="Version">
<img src="https://img.shields.io/badge/Python-3.10%2B-2B2B2B?style=for-the-badge&logo=python&logoColor=F5B041" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-Web%20Framework-2B2B2B?style=for-the-badge&logo=fastapi&logoColor=F5B041" alt="FastAPI">
<img src="https://img.shields.io/badge/SQLite-Database-2B2B2B?style=for-the-badge&logo=sqlite&logoColor=F5B041" alt="SQLite">
<img src="https://img.shields.io/badge/Docker-HTTPS%20Ready-2B2B2B?style=for-the-badge&logo=docker&logoColor=F5B041" alt="Docker">
<br>
<img src="https://img.shields.io/badge/Testler-96%20ge%C3%A7ti-4F6B2F?style=for-the-badge&logo=pytest&logoColor=white" alt="Testler">
<img src="https://img.shields.io/badge/Giri%C5%9F-E--posta%20%7C%20Google%20%7C%20GitHub%20%7C%20Microsoft%20%7C%20Apple-2B2B2B?style=for-the-badge" alt="Giriş">
<img src="https://img.shields.io/badge/Aray%C3%BCz-Gizli%20Dosya-9E1F17?style=for-the-badge" alt="Arayüz">
<img src="https://img.shields.io/badge/License-Educational-C9A227?style=for-the-badge" alt="License">
<img src="https://img.shields.io/badge/Maskot-Rakun%20%F0%9F%A6%9D-E8751A?style=for-the-badge" alt="Maskot: Rakun">
<br>
<img src="https://img.shields.io/badge/MITRE-ATT%26CK-9E1F17?style=for-the-badge" alt="MITRE ATT&CK">
<img src="https://img.shields.io/badge/AI%20Analist-Claude-2B2B2B?style=for-the-badge" alt="AI Analist">
<img src="https://img.shields.io/badge/Uyum-ISO%2027001%20%7C%20KVKK-4F6B2F?style=for-the-badge" alt="Uyum">
</p>

<p align="center">
<a href="#-60-saniyede-başla">Hızlı Başlangıç</a> •
<a href="#️-ekran-turu">Ekran Turu</a> •
<a href="#-derin-analiz-v80-cortex">v8 Cortex</a> •
<a href="#-sürekli-izleme-v70">İzleme</a> •
<a href="#️-nasıl-çalışır">Nasıl Çalışır</a> •
<a href="#-api">API</a> •
<a href="#-alan-adında-yayınlama-https">Yayınlama</a> •
<a href="#-neden-rakun">Maskot</a> •
<a href="#-sorun-giderme">Sorun Giderme</a> •
<a href="#️-yol-haritası">Yol Haritası</a> •
<a href="docs/YARISMA.md">TÜBİTAK / TEKNOFEST</a>
</p>

<p align="center">
<img src="docs/screenshots/02-operasyon-merkezi.jpg" alt="ReconClaw Operasyon Merkezi" width="100%">
</p>

> [!IMPORTANT]
> ReconClaw yalnızca **sahibi olduğunuz** veya **yazılı izin aldığınız** sistemlerde kullanılmalıdır. İzinsiz port taraması Türkiye'de TCK 243–245 kapsamında suç teşkil edebilir. Ayrıntılar için [Yasal Uyarı](#️-yasal-uyarı) bölümüne bakın.

---

## 📑 İçindekiler

<details>
<summary><b>Tüm başlıkları göster</b></summary>

- [ReconClaw Nedir?](#-reconclaw-nedir)
- [60 Saniyede Başla](#-60-saniyede-başla)
- [Ekran Turu](#️-ekran-turu)
  - [Erişim Terminali (Giriş)](#1-erişim-terminali-giriş)
  - [Operasyon Merkezi](#2-operasyon-merkezi)
  - [Yeni Tarama: Radar ve Terminal](#3-yeni-tarama-radar-ve-terminal)
  - [Hedef Dosyası](#4-hedef-dosyası)
  - [Karşılaştırma](#5-karşılaştırma)
  - [Ağ Krokisi](#6-ağ-krokisi)
  - [Arşiv](#7-arşiv)
  - [Komut Paleti ve Kısayollar](#8-komut-paleti-ve-kısayollar)
  - [Bildirimler](#9-bildirimler)
  - [Ayarlar](#10-ayarlar)
  - [PDF Rapor](#11-pdf-rapor)
  - [Kâğıt Tema ve Vurgu Renkleri](#12-kâğıt-tema-ve-vurgu-renkleri)
  - [Telefon](#13-telefon)
- [Derin Analiz (v8.0 Cortex)](#-derin-analiz-v80-cortex)
  - [Güvenlik karnesi](#-güvenlik-karnesi-a--f)
  - [MITRE ATT&CK eşlemesi](#-mitre-attck-eşlemesi-ve-saldırı-zinciri)
  - [ISO 27001 / KVKK uyumu](#-iso-27001--kvkk-uyum-ön-değerlendirmesi)
  - [AI Analist](#-ai-analist)
  - [Paylaşım bağlantısı](#-salt-okunur-paylaşım-bağlantısı)
- [Sürekli İzleme (v7.0)](#-sürekli-izleme-v70)
- [Pasif Keşif (v7.0)](#️-pasif-keşif-v70)
- [Yönetim Paneli ve Admin Hesabı](#-yönetim-paneli-ve-admin-hesabı)
- [Abonelik Planları](#-abonelik-planları)
- [Nasıl Çalışır?](#️-nasıl-çalışır)
- [Risk Değerlendirme Modeli](#-risk-değerlendirme-modeli)
- [Eklentiler](#-eklentiler)
- [API](#-api)
- [Yapılandırma (.env)](#️-yapılandırma-env)
- [Alan Adında Yayınlama (HTTPS)](#-alan-adında-yayınlama-https)
- [Güvenlik](#️-güvenlik)
- [Neden Rakun?](#-neden-rakun)
- [Sürüm Geçmişi](#-sürüm-geçmişi)
- [Proje Yapısı](#-proje-yapısı)
- [Veritabanı](#-veritabanı)
- [Testler](#-testler)
- [Sorun Giderme](#-sorun-giderme)
- [Sunum Rehberi](#-sunum-rehberi)
- [Yol Haritası](#️-yol-haritası)
- [Yasal Uyarı](#️-yasal-uyarı)
- [TÜBİTAK / TEKNOFEST proje dosyası](docs/YARISMA.md)

</details>

---

## 🦝 ReconClaw Nedir?

ReconClaw; **yetkili** ağ keşfi (reconnaissance), port analizi, servis tespiti ve ön güvenlik değerlendirmesi için geliştirilmiş, web arayüzlü bir siber güvenlik platformudur. Bir hedefi verirsiniz; ReconClaw portlarını saniyeler içinde yoklar, açık servislerin sürümünü yakalar, bilinen zafiyetlerle eşleştirir, bir **risk skoru** ve **A+…F güvenlik notu** hesaplar, bulguları **MITRE ATT&CK** saldırı zincirine ve **ISO 27001 / KVKK** kontrollerine bağlar, **AI Analist** ile ne yapmanız gerektiğini Türkçe olarak söyler ve hedefi **sürekli izleyerek** değişiklikte alarm verir. Hepsi, bir istihbarat dosyası gibi tasarlanmış tek bir panelde.

| | Ne yapar? | Nasıl? |
|---|-----------|--------|
| ⚡ | **Hızlı keşif** | Asenkron TCP motoru yüzlerce portu aynı anda, eşzamanlılık sınırıyla yoklar |
| 🔍 | **Sürüm tespiti** | Banner grabbing ile servisin kendini tanıttığı satırı yakalar (SSH, FTP, HTTP…) |
| 🔴 | **Zafiyet eşleştirme** | Banner'ları CVE imzalarıyla karşılaştırır (vsFTPd 2.3.4, eski OpenSSH, Apache 2.4.49…) |
| 🧩 | **Derin kontrol** | Eklentiler HTTP güvenlik başlıklarını ve TLS sertifikalarını denetler |
| 🧠 | **Risk skoru** | Servis kritikliği + CVE + eklenti bulgularından 0–100 arası skor |
| ✅ | **Öneri** | Her bulgu için somut adım: "MySQL'i dış ağa kapat", "SFTP'ye geç"… |
| ⇄ | **Değişim takibi** | Aynı hedefin iki taramasını karşılaştırır: açılan / kapanan portlar, çözülen bulgular |
| 🖨️ | **Raporlama** | GİZLİ damgalı PDF rapor, CSV ve JSON dışa aktarım |
| 🔐 | **Çok kullanıcılı** | E-posta veya Google / GitHub / Microsoft / Apple ile giriş; herkes yalnızca kendi taramalarını görür |
| 🌐 | **Yayına hazır** | Docker + Caddy ile alan adında tek komutla otomatik HTTPS |
| 🎯 | **MITRE ATT&CK** *(v8)* | Açık servisleri 14 taktiklik matristeki tekniklere bağlar, keşiften etkiye **saldırı zinciri** çizer |
| 🅰️ | **Güvenlik karnesi** *(v8)* | 5 kategoride puanlama ve A+…F not; kritik sorunlar notu tavanlar |
| ⚖️ | **Uyum** *(v8)* | ISO/IEC 27001:2022 Ek A ve KVKK m.12 için uyumlu / kısmi / uyumsuz ön değerlendirme |
| 🤖 | **AI Analist** *(v8)* | Claude ile Türkçe yönetici özeti, önceliklendirilmiş aksiyon planı ve rapor üzerine soru-cevap; internetsiz ortamda kural tabanlı analist |
| 📡 | **Sürekli izleme** *(v7)* | Saatlik / günlük / haftalık otomatik tarama, değişim alarmı, Discord / Slack webhook |
| 🛰️ | **Pasif keşif** *(v7)* | Sertifika Şeffaflığı loglarından alt alan adları, DNS kayıtları, SPF / DMARC / CAA denetimi |
| 👑 | **Yönetim paneli** *(v7)* | Kullanıcılar, plan atama, askıya alma, gelir özeti ve denetim kaydı |

**Kimler için?** Ağını tanımak isteyen sistem yöneticileri, siber güvenlik öğrencileri, CTF / lab ortamlarında çalışanlar ve yetkili sızma testi öncesinde hızlı bir ön değerlendirme isteyenler için.

---

## 🚀 60 Saniyede Başla

> Gereksinim: **Python 3.10+** ve **git**. (Kali Linux, Ubuntu, macOS ve Windows'ta çalışır.)

```bash
# 1) Projeyi indir
git clone https://github.com/Pireburak/ReconClaw.git
cd ReconClaw

# 2) Sanal ortamı kur ve bağımlılıkları yükle
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3) Ayar dosyasını oluştur (varsayılanlarla da çalışır)
cp .env.example .env

# 4) Çalıştır
python main.py
```

Tarayıcıda **http://127.0.0.1:8000** adresini açın, ardından:

1. **KAYIT OL** sekmesinden bir operatör hesabı açın.
2. Sol raydaki 🔍 ikonuna (veya `1` tuşuna) basıp **Yeni Tarama** sayfasına geçin.
3. Hedefe `scanme.nmap.org` yazın. Bu, Nmap'in tarama için resmi olarak izin verdiği test sunucusudur.
4. **TARAMAYI BAŞLAT** deyin ve radarı izleyin. 🦝

> [!TIP]
> Sonraki açılışlarda yalnızca şu üç satır yeterlidir:
> ```bash
> cd ~/ReconClaw && source .venv/bin/activate && python main.py
> ```

---

## 🖼️ Ekran Turu

> Görüntüler yerel bir test laboratuvarında (127.0.0.1 üzerinde kasıtlı olarak eski sürümlü sahte servisler) alınmıştır.

### 1. Erişim Terminali (Giriş)

<p align="center"><img src="docs/screenshots/01-erisim-terminali.jpg" alt="Erişim terminali" width="100%"></p>

Giriş ekranı, açık bir istihbarat dosyası gibi tasarlandı:

- **Solda dosya künyesi:** dosya numarası, konu, sınıf ve karartılmış (██████) bir "Kaynak" satırı. Altında **Keşif / Analiz / Rapor** sekmeli yetenek özeti.
- **Sağda kimlik doğrulama:** kayan etiketli e-posta ve parola alanları, parolayı göster/gizle, kayıt modunda **parola gücü göstergesi**.
- **Sosyal giriş:** Google, GitHub, Microsoft ve Apple. Yapılandırılmamış olanlar pasif görünür.
- **Arka plan:** WebGL ile çizilen, yavaşça kayan bir **topoğrafik harita**. Farenin altında bir tepe oluşur. WebGL yoksa düz arka plana düşer; sekme arka plandayken çizim durur.
- Köşede kırmızı **GİZLİ** damgası, üstte ve altta sınıflandırma bandı.

<details>
<summary>📄 Kâğıt temada erişim terminali</summary>
<p align="center"><img src="docs/screenshots/14-erisim-kagit.jpg" alt="Kâğıt temada erişim terminali" width="100%"></p>
</details>

### 2. Operasyon Merkezi

<p align="center"><img src="docs/screenshots/02-operasyon-merkezi.jpg" alt="Operasyon merkezi" width="100%"></p>

Girişten sonra açılan genel bakış ekranı, tüm taramalarınızın özetidir:

| Bölüm | Gösterdiği |
|-------|------------|
| **Yetenek özeti** | Keşif / Analiz / Güvenlik & Rapor sekmeli kartlar. Her kart ilgili sayfaya götürür; ✕ ile gizlenir |
| **İstatistik kartları** | Hedef, zafiyet, kritik bulgu, yüksek riskli hedef, aktif tarama ve veritabanı durumu. Rakamlar sayarak artar, kartın altında mini trend çizgisi (sparkline) vardır |
| **01 Tehdit değerlendirmesi** | Ortalama risk halkası + şiddete göre bulgu dağılımı (kritik / yüksek / orta / düşük) |
| **02 Olay kaydı** | En yeni CVE eşleşmeleri ve yüksek/orta bulgular; tıklayınca ilgili rapor açılır |
| **03 Risk eğilimi** | Son 20 taramanın risk skoru (çizgi) ve bulgu sayısı (sütun) |
| **04 En çok açık port** | Hedefleriniz arasında en sık açık bulunan portlar |
| **05 Operasyon takvimi** | GitHub tarzı, son 1 yılın gün gün tarama yoğunluğu |
| **06 Hedef risk tablosu** | Her hedefin en güncel taraması, riske göre sıralı |

Üstteki **durum satırı** ağ geçidi, tarama motoru ve veritabanı durumunu, UTC saatini ve sunucunun çalışma süresini gösterir. Panel açıkken her 15 saniyede bir kendini yeniler.

### 3. Yeni Tarama: Radar ve Terminal

<p align="center"><img src="docs/screenshots/03-yeni-tarama.jpg" alt="Yeni tarama" width="100%"></p>

- **Hedef:** IP adresi veya alan adı. `https://site.com/yol` gibi girdiler otomatik temizlenir.
- **Port kapsamı:** *Yaygın portlar* (güvenlik açısından kritik 27 port) ya da *1 → Maks. port* (65535'e kadar).
- **Zaman aşımı** (0.2–5 sn) ve **eklentiler** açık/kapalı.
- Son taranan hedefler altta **tek tıkla yeniden tarama** çipleri olarak durur.
- Tarama sürerken **radar** döner ve geçen süreyi gösterir. Bitince her açık port, risk rengine göre radarda parlayan bir nokta olarak belirir.
- **Terminal** her adımı zaman damgasıyla yazar: DNS çözümü, açık portlar, banner'lar, CVE uyarıları ve eklenti bulguları.

### 4. Hedef Dosyası

<p align="center"><img src="docs/screenshots/04-hedef-dosyasi.jpg" alt="Hedef dosyası" width="100%"></p>

Bir taramanın tam raporu:

- **Risk göstergesi:** 270°'lik, işaret çizgili, dolarak gelen yay ve seviye etiketi
- **Künye:** hedef, IP (tek tıkla kopyala), açık port / taranan port, süre, tarih
- **Port tablosu:** servis, sürüm/banner ve her port için animasyonlu risk çubuğu
- **Dışa aktarma:** JSON · CSV · PDF rapor · Öncekiyle karşılaştır · Ağ krokisi · Tekrar tara

<p align="center"><img src="docs/screenshots/05-bulgular.jpg" alt="CVE uyarıları, öneriler ve eklenti bulguları" width="100%"></p>

Aşağıda **CVE uyarıları**, **öneriler** ve **eklenti bulguları** yer alır. Bulgular şiddete göre tek tıkla süzülebilir (Tümü / Orta / Düşük / Bilgi).

### 5. Karşılaştırma

<p align="center"><img src="docs/screenshots/06-karsilastirma.jpg" alt="Tarama karşılaştırma" width="100%"></p>

Aynı hedefin iki taramasını yan yana koyar ve **ne değişti** sorusunu cevaplar:

- Risk skorundaki değişim (artış kırmızı, düşüş yeşil)
- **Yeni açılan** ve **kapanan** portlar
- **Sürümü değişen** servisler (ör. `OpenSSH_5.3` → `OpenSSH_9.6`)
- **Yeni** ve **çözülen** bulgular / CVE'ler

Hedef dosyasındaki **ÖNCEKİYLE KARŞILAŞTIR** butonu ya da arşivde iki kutuyu işaretlemek yeterlidir. Farklı hedefler seçilirse uyarı verir.

### 6. Ağ Krokisi

<p align="center"><img src="docs/screenshots/07-ag-krokisi.jpg" alt="Ağ krokisi" width="100%"></p>

Hedefi merkeze, açık portlarını etrafına yerleştiren bir topoloji çizimi:

- Düğüm çerçeve rengi = portun risk seviyesi
- **Kesikli kırmızı hat** = o portta CVE veya yüksek şiddetli bulgu var
- Düğüm üzerindeki rozet = bulgu sayısı
- Bir porta tıklayınca diğerleri solar, sağ panelde **banner, CVE ve bulgular** açılır. `Enter` ile klavyeden de gezilebilir.

### 7. Arşiv

<p align="center"><img src="docs/screenshots/08-arsiv.jpg" alt="Operasyon arşivi" width="100%"></p>

Tüm taramalar en yeniden eskiye listelenir. Hedef veya IP'ye göre **anlık arama** yapılabilir (`/` tuşu). Satıra tıklayınca rapor açılır, iki kutu işaretlenince **karşılaştırılır**, ✕ ile tek tek silinir.

### 8. Komut Paleti ve Kısayollar

<p align="center"><img src="docs/screenshots/10-komut-paleti.jpg" alt="Komut paleti" width="100%"></p>

**Ctrl+K** ile açılan komut paleti, fareye dokunmadan her şeyi yapmanızı sağlar: bölümlere gitmek, temayı veya vurgu rengini değiştirmek, son raporu PDF/CSV almak, eski raporları açmak, bir hedefi tek tuşla yeniden taramak. Palete listede olmayan bir hedef yazıp `Enter`'a basarsanız doğrudan tarama sayfasına gider.

| Kısayol | İşlev |
|---------|-------|
| `Ctrl` + `K` | Komut paleti |
| `0` … `9` | Bölümler arasında geçiş (0 = Operasyon Merkezi, 6 = Pasif Keşif, 7 = Sürekli İzleme, 8 = Ayarlar, 9 = Abonelik) |
| `A` | Yönetim paneli (yalnızca yöneticiler) |
| `N` | Yeni tarama |
| `T` | Karanlık / kâğıt tema |
| `/` | Arşivde ara |
| `?` | Kısayol listesi |
| `Esc` | Açık pencereyi kapat |

### 9. Bildirimler

<p align="center"><img src="docs/screenshots/11-bildirimler.jpg" alt="Bildirim zili" width="100%"></p>

Üstteki zil, **görülmemiş kritik ve yüksek** olayların sayısını gösterir. Tıklayınca liste açılır ve sayaç sıfırlanır; bir olaya tıklayınca ilgili rapor açılır.

### 10. Ayarlar

<p align="center"><img src="docs/screenshots/09-ayarlar.jpg" alt="Ayarlar" width="100%"></p>

| Kart | İçerik |
|------|--------|
| **Görünüm** | Karanlık / Kâğıt / Sistem teması, 5 vurgu rengi, özellik tanıtımını aç/kapa |
| **Tarama varsayılanları** | Port kapsamı, maks. port, zaman aşımı, eklentiler (tarayıcıda saklanır) |
| **Profil** | Ad, e-posta, bağlı giriş yöntemleri |
| **Güvenlik** | Parola değiştir / belirle, **diğer cihazlardan çıkış** |
| **API erişimi** | Kişisel API anahtarı oluştur / iptal et, hazır `curl` örneği |
| **Tehlikeli bölge** | Tüm tarama geçmişini sil, hesabı kalıcı olarak sil |

### 11. PDF Rapor

<p align="center"><img src="docs/screenshots/13-pdf-rapor.jpg" alt="GİZLİ damgalı PDF rapor" width="80%"></p>

Her tarama, yazdırılabilir bir **güvenlik değerlendirme dosyasına** dönüşür: dosya numarası, **GİZLİ** damgası, sınıflandırma bantları, yönetici özeti, port tablosu, CVE uyarıları, eklenti bulguları ve öneriler. Tarayıcıdan **Yazdır → PDF olarak kaydet** ile dosya hâline gelir. Teslim edilecek ödev ve raporlar için idealdir.

### 12. Kâğıt Tema ve Vurgu Renkleri

<p align="center"><img src="docs/screenshots/12-kagit-tema.jpg" alt="Kâğıt tema" width="100%"></p>

`T` tuşuyla karanlık tema, sararmış bir **kâğıt dosyaya** dönüşür. Ayarlar'dan 5 vurgu rengi seçilebilir:

| Renk | Karanlık | Kâğıt |
|------|----------|-------|
| **Mürekkep** (varsayılan) | Kâğıt beyazı | Siyah mürekkep |
| **Bakır** | `#d98a3a` | `#9c4a14` |
| **Sinyal kırmızısı** | `#e5484d` | `#b42318` |
| **Haki** | `#a3b86c` | `#4f6b2f` |
| **Çelik mavisi** | `#86aed4` | `#2f5f8f` |

Tema ve renk tercihi tarayıcıda saklanır. Sayfa açılırken erken yüklendiği için yanlış renkte yanıp sönme olmaz.

### 13. Telefon

<p align="center"><img src="docs/screenshots/15-mobil.jpg" alt="Telefon görünümü" width="320"></p>

Arayüz telefonda da tam çalışır: sol ikon rayı ekranın altına **sekme çubuğu** olarak iner, tablolar yatay kaydırılır, giriş ekranında form üste, dosya özeti alta geçer.

---

## 🧠 Derin Analiz (v8.0 Cortex)

v8.0 ile her tarama raporunun altına **Derin analiz** paneli geldi. Panel aynı rapora dört farklı mercekten bakar: **Karne**, **MITRE ATT&CK**, **Uyum** ve **AI Analist**. İlk üçü tamamen çevrimdışı ve deterministiktir (aynı rapor her zaman aynı sonucu verir); kodu `core/intel.py` içinde ve testlerle doğrulanmıştır. Bu bölümler PDF rapora ve paylaşım bağlantısına da girer.

### 🏅 Güvenlik karnesi (A+ … F)

<p align="center"><img src="docs/screenshots/19-guvenlik-karnesi.jpg" alt="Güvenlik karnesi" width="100%"></p>

| Kategori | Ağırlık | Neye bakar? |
|----------|:-------:|-------------|
| Ağ maruziyeti | %30 | Veritabanı, SMB, RDP, VNC, Telnet gibi dışarıda olmaması gereken servisler (−25), yönetim servisleri (−6) |
| Yama düzeyi | %30 | Bilinen CVE imzası başına −45 |
| Şifreleme | %20 | FTP / Telnet / POP3 / IMAP gibi şifresiz kimlik doğrulama, yalnızca HTTP sunulması, TLS bulguları, eksik HSTS |
| Web sıkılaştırma | %10 | HTTP güvenlik başlıkları (yalnızca web servisi varsa hesaplanır) |
| Bilgi ifşası | %10 | Banner'da veya `Server:` başlığında sürüm bilgisi |

Not ölçeği: **A+** ≥95 · **A** ≥85 · **B** ≥70 · **C** ≥55 · **D** ≥40 · **F**. SSL Labs'teki yaklaşım gibi kritik sorunlar notu **tavanlar**: bilinen CVE varken not en fazla **D**, veritabanı veya dosya paylaşımı dışarıya açıkken en fazla **C** olabilir.

### 🎯 MITRE ATT&CK eşlemesi ve saldırı zinciri

<p align="center"><img src="docs/screenshots/20-mitre-attack.jpg" alt="MITRE ATT&CK matrisi" width="100%"></p>

Her açık servis ve bulgu, bir saldırganın o hedefte kullanabileceği **ATT&CK Enterprise** tekniklerine bağlanır (ör. SSH açık → T1133 Dış uzak erişim servisleri, T1110 Kaba kuvvet, T1021.004 SSH ile yanal hareket; CVE imzası → T1190 Dışa açık uygulamanın istismarı). Sonuç 14 taktiklik bir matriste gösterilir; bir tekniğe tıklayınca gerekçesi ve attack.mitre.org bağlantısı açılır.

Üstteki ok zinciri, matris sırasıyla her taktikten **tek bir teknik** seçerek oluşturulan **olası saldırı yoludur** (kill chain). Etkisi büyük teknikler (CVE istismarı, fidye amaçlı şifreleme, veri imhası) önceliklidir ve bir teknik zincirde yalnızca bir kez yer alır.

### 📋 ISO 27001 / KVKK uyum ön değerlendirmesi

<p align="center"><img src="docs/screenshots/21-uyum.jpg" alt="Uyum ön değerlendirmesi" width="100%"></p>

ISO/IEC 27001:2022 Ek A'dan dışarıdan gözlemlenebilen 8 kontrol (A.8.5, A.8.8, A.8.9, A.8.16, A.8.20, A.8.21, A.8.22, A.8.24) ve 6698 sayılı KVKK'nın **12. maddesi** (veri güvenliğine ilişkin yükümlülükler) için **uyumlu / kısmi / uyumsuz** sınıflandırması ve kanıt üretilir. Hedef sürekli izlemedeyse A.8.16 (izleme faaliyetleri) uyumlu sayılır.

> [!NOTE]
> Uyum çıktısı yalnızca dışarıdan görülebilen bulgulara dayanan **otomatik bir ön değerlendirmedir**; resmi denetimin yerini tutmaz.

### 🤖 AI Analist

<p align="center"><img src="docs/screenshots/22-ai-analist.jpg" alt="AI Analist" width="100%"></p>

**Değerlendirme üret** düğmesi raporu; **Yönetici özeti**, **Saldırgan gözünden**, **Öncelikli aksiyon planı** (P1 · 24 saat, P2 · 1 hafta, P3 · 30 gün) ve **Uyum notu** bölümleriyle yorumlar. Alttaki kutudan rapor hakkında soru sorabilirsiniz ("3306 neden riskli?", "KVKK açısından durum ne?").

| Motor | Ne zaman? | Nasıl? |
|-------|-----------|--------|
| **Claude** | `.env` içinde `ANTHROPIC_API_KEY` tanımlıysa | Rapor, karne, ATT&CK zinciri ve uyum sonucu resmi `anthropic` Python SDK'sıyla `claude-opus-5-5` modeline gönderilir. Model bir isteği reddederse API'nin sunucu taraflı yedek modeli (`fallbacks: "default"`) devreye girer |
| **Kural tabanlı** | Anahtar yoksa, internet yoksa veya API hata verirse | Aynı bölümleri deterministik kurallarla üretir; port numarası içeren soruları yanıtlar. Sunumda internet olmasa da çalışır |

- **İstem enjeksiyonu (prompt injection) koruması:** Banner ve HTTP başlıkları taranan sunucudan, yani potansiyel saldırgandan gelir. Bu veriler modele ayrı bir `<rapor_verisi>` bloğunda verilir ve sistem talimatı, bloktaki metinlerin talimat olarak değil yalnızca veri olarak ele alınmasını söyler.
- Rapor değerlendirmesi önbelleğe alınır; aynı raporu tekrar açmak kota harcamaz. Günlük AI hakkı plana bağlıdır (Pro Max 20, Ultra 100, Ultra Max 500).

### 🔗 Salt-okunur paylaşım bağlantısı

<p align="center"><img src="docs/screenshots/23-paylasilan-rapor.jpg" alt="Paylaşılan rapor" width="100%"></p>

Sonuç sayfasındaki **PAYLAŞ** düğmesi, raporu oturum açmadan görüntülenebilen bir bağlantıya (`/share/<anahtar>`) dönüştürür: jüriye, müşteriye veya ekibe gönderin. Bağlantı 192 bit rastgele anahtar taşır, arama motorlarına kapalıdır (`X-Robots-Tag: noindex`) ve tek tıkla iptal edilir.

<p align="center"><img src="docs/screenshots/27-mobil-karne.jpg" alt="Telefonda güvenlik karnesi" width="320"></p>

---

## 📡 Sürekli İzleme (v7.0)

<p align="center"><img src="docs/screenshots/24-surekli-izleme.jpg" alt="Sürekli izleme" width="100%"></p>

Bir hedefi **saatlik, günlük veya haftalık** izlemeye alın. Arka plandaki zamanlayıcı zamanı gelen görevi tarar, sonucu bir önceki taramayla karşılaştırır ve değişiklikleri alarm olarak kaydeder:

| Alarm | Şiddet |
|-------|--------|
| Yeni açılan veritabanı / SMB / RDP / VNC / Telnet portu | 🔴 Kritik |
| Yeni CVE imzası | 🔴 Kritik |
| Diğer yeni açık portlar, risk skorunda +10 ve üzeri artış | 🟠 Yüksek |
| Servis sürümü değişikliği, yeni orta/yüksek eklenti bulgusu | 🟡 Orta |
| Kapanan port, giderilen zafiyet | ⚪ Bilgi |

Alarmlar **İzleme** sayfasındaki akışta ve üst bardaki 🔔 zilde görünür. Görev tanımlarken bir **webhook** adresi verirseniz önemli değişiklikler Discord, Slack veya kendi sunucunuza JSON olarak gönderilir. İzleme taramaları günlük kotaya sayılır ve hedef doğrulama kurallarına uyar; plan izlemeyi kapsamazsa görev kendiliğinden duraklatılır.

---

## 🛰️ Pasif Keşif (v7.0)

<p align="center"><img src="docs/screenshots/25-pasif-kesif.jpg" alt="Pasif keşif" width="100%"></p>
<p align="center"><sub>Görseldeki veriler, IANA'nın örnek kullanım için ayırdığı <code>example.com</code> üzerinde hazırlanmış <b>örnek veridir</b>.</sub></p>

Hedefe **tek bir paket göndermeden** saldırı yüzeyini çıkarır:

- **Alt alan adları:** Bir alan adı için verilmiş her TLS sertifikası herkese açık **Sertifika Şeffaflığı** loglarına yazılır. ReconClaw bunları crt.sh'tan (yanıt vermezse CertSpotter'dan) toplar ve DNS'te çözülüp çözülmediğini kontrol eder.
- **Dikkat çeken adlar:** `admin`, `dev`, `staging`, `vpn`, `jenkins`, `grafana` gibi saldırganların ilk baktığı adlar kırmızı etiketle işaretlenir.
- **DNS ve e-posta güvenliği:** A, AAAA, MX, NS, TXT, CAA kayıtları DNS-over-HTTPS ile alınır; **SPF** (katı / esnek / tehlikeli), **DMARC** (none / quarantine / reject) ve **CAA** değerlendirilip 0–100 e-posta güvenlik puanı verilir.
- Her alt alan adının yanındaki **TARA** aktif port taramasını, **İZLE** günlük izleme görevini başlatır.

MITRE ATT&CK karşılığı: T1596.003 (Digital Certificates) ve T1590.002 (DNS).

---

## 👑 Yönetim Paneli ve Admin Hesabı

<p align="center"><img src="docs/screenshots/26-yonetim-paneli.jpg" alt="Yönetim paneli" width="100%"></p>

Yönetici hesapları **sınırsız "Admin" seviyesindedir** (kota, port, izleme ve AI sınırı yoktur) ve sol menüde kırmızı kalkanlı **YÖNETİM** sayfasını görür (kısayol `A`):

- **Sistem özeti:** kullanıcı sayısı, ücretli abone, aylık yinelenen gelir (MRR), tahsilat, bugünkü tarama, aktif izleme, son 24 saatteki hatalı giriş, 14 günlük kayıt / tarama grafiği
- **Kullanıcılar:** arama, ödeme kaydı oluşturmadan plan atama (30 gün / 1 yıl / süresiz), yönetici yapma, askıya alma (oturumlar ve API anahtarı anında geçersiz olur), silme
- **Denetim kaydı:** giriş, hatalı giriş, plan değişikliği, API anahtarı ve yönetici eylemleri; IP adresi ve işlemi yapan kişiyle

Yönetici kendini askıya alamaz, yetkisini kaldıramaz veya silemez; böylece sistem yöneticisiz kalmaz.

**Panel gizlidir (v8.2):** Yönetici olmayan kullanıcılar ve oturumsuz ziyaretçiler için panel hiç yokmuş gibi davranır. Menüde görünmez, sayfa kaynağında ve herkese giden JavaScript'te izi yoktur (`admin.js` yalnızca yöneticilere yüklenir), `/api/admin/*` uç noktaları **404** döner ve `/docs` API belgesinde listelenmez. Asıl koruma ise sunucunun her istekte rolü denetlemesidir. Her kullanıcı kendi hesap etkinliğini **Ayarlar → Hesap etkinliği**'nde görür.

**Kendinizi yönetici yapmak için** (önce siteye normal şekilde kayıt olun):

```bash
# Yöntem 1: komut satırı (anında)
python manage.py make-admin sizin@mailiniz.com

# Yöntem 2: .env dosyası (sunucu yeniden başlatılınca)
ADMIN_EMAILS=sizin@mailiniz.com
```

> [!TIP]
> Güvenlik gereği parolayla açılan bir hesap, `ADMIN_EMAILS` listesinde olsa bile **kayıt anında** yönetici olmaz (e-posta doğrulanmadığı için adresi sizden önce alan biri yönetici olabilirdi). Hesap sunucu açılırken veya `manage.py` ile yükseltilir. E-postası sağlayıcı tarafından doğrulanmış Google / GitHub girişi ise anında yönetici olur.

---

## 💳 Abonelik Planları

ReconClaw **5 kademeli üyelik** sistemine sahiptir. Her yeni hesap **Free** planla başlar; sınırlar yalnızca arayüzde değil **sunucu tarafında** uygulanır (API ile de aşılamaz). Sınırı aşan bir istek `HTTP 402` döner ve arayüz kullanıcıyı **Abonelik** sayfasına yönlendirir. **Sınırsız erişim yalnızca yöneticilere** (Admin seviyesi) aittir; hiçbir satın alınabilir plan sınırsız değildir.

<p align="center"><img src="docs/screenshots/16-abonelik.jpg" alt="Abonelik planları" width="100%"></p>

| Özellik | 🆓 Free | ⭐ Pro | 💎 Pro Max | 🚀 Ultra | 👑 Ultra Max | 🛡️ Admin |
|---------|:------:|:-----:|:---------:|:-------:|:-----------:|:-------:|
| **Aylık fiyat** | **₺0** | **₺299** | **₺599** | **₺999** | **₺1.999** | satın alınamaz |
| Yıllık fiyat *(2 ay bedava)* | ₺0 | ₺2.990 | ₺5.990 | ₺9.990 | ₺19.990 | — |
| Günlük tarama | 5 | 50 | 200 | 1.000 | 5.000 | ∞ |
| Dakikalık tarama | 2 | 5 | 10 | 20 | 60 | ∞ |
| Port aralığı | 1–100 | 1–1024 | 1–10000 | 1–65535 | 1–65535 | 1–65535 |
| HTTP / TLS eklentileri | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| PDF / CSV rapor, paylaşım bağlantısı | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tarama karşılaştırma | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| API anahtarı | — | — | ✅ | ✅ | ✅ | ✅ |
| Doğrulanmış hedef | 1 | 3 | 10 | 25 | 100 | ∞ |
| Pasif keşif (CT / DNS) | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sürekli izleme | — | 1 görev | 5 görev | 20 görev | 50 görev | ∞ |
| Saatlik izleme | — | — | — | ✅ | ✅ | ✅ |
| AI Analist | — | — | 20 / gün | 100 / gün | 500 / gün | ∞ |
| Güvenlik karnesi, ATT&CK, uyum | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 🌍 Bölgesel fiyatlandırma (v8.1)

<p align="center"><img src="docs/screenshots/28-bolgesel-fiyat.jpg" alt="Bölgesel fiyatlandırma" width="100%"></p>

Fiyatlar ziyaretçinin **IP adresinin ülkesine** göre yerel para biriminde gösterilir: Almanya ve Avro Bölgesi **€**, ABD **$**, Birleşik Krallık **£**, Suudi Arabistan **SAR**, BAE **AED**, Katar, Kuveyt, Azerbaycan, İsviçre, Japonya, Kanada, Avustralya ve Rusya kendi para birimiyle; listede olmayan ülkeler **$** ile.

- **En ucuz fiyat her zaman Türkiye'dedir.** Yurt dışında her ücretli planın aylık fiyatına **≈950 TL** (`REGIONAL_SURCHARGE_TRY`) eklenir, güncel kurla çevrilir ve x,99 biçimine yuvarlanır. Örnek: Pro = (299 + 950) TL ÷ kur → Almanya'da yaklaşık **€24,99**.
- Kurlar open.er-api.com'dan 12 saatte bir alınır; internet yoksa `.env`'deki `FX_RATES` veya yerleşik yaklaşık kurlar kullanılır.
- Abonelik sayfasındaki **BÖLGE** menüsünden başka ülkelerin fiyatları önizlenebilir; **ödeme ise her zaman IP'den tespit edilen bölgenin fiyatıyla** alınır (VPN'siz biri Türkiye fiyatı seçemez). Ödeme kaydı para birimi, ülke ve TL karşılığıyla saklanır; yönetim panelindeki gelir TL'ye çevrilerek toplanır.
- Yerel ağdan (127.0.0.1, 192.168.x) bağlananlar Türkiye (`DEFAULT_COUNTRY`) sayılır. Cloudflare arkasında `TRUST_COUNTRY_HEADER=true` ile `CF-IPCountry` başlığı kullanılır.

- **Günlük kota** ayrı bir sayaçta tutulur: tarama silmek hakkı geri vermez. İzleme taramaları da kotaya sayılır.
- Ücretli planın süresi dolunca hesap otomatik olarak **Free** sınırlarına döner; API anahtarı da çalışmayı bırakır.
- Üst barda planı gösteren rozet ve `KOTA 3/5` sayacı bulunur; kilitli düğmelerde **PRO** etiketi görünür.

<table>
<tr>
<td width="50%"><img src="docs/screenshots/17-odeme.png" alt="Demo ödeme onayı"></td>
<td width="50%"><img src="docs/screenshots/18-yukselt.png" alt="Plan yükseltme penceresi"></td>
</tr>
<tr>
<td align="center"><sub>Demo ödeme onayı</sub></td>
<td align="center"><sub>Kilitli özellikte yükseltme penceresi</sub></td>
</tr>
</table>

> [!NOTE]
> Ödeme şimdilik **demo modundadır**: kart bilgisi istenmez ve saklanmaz, plan anında etkinleşir ve `payments` tablosuna `demo` durumlu bir kayıt düşülür. Gerçek ödeme altyapısı (iyzico, Lemon Squeezy vb.) `core/plans.py` içindeki `checkout()` fonksiyonunun yerine bağlanacak şekilde tasarlandı.

### 🎯 Hedef sahipliği doğrulama

İnternete açık bir sunucuda kimsenin başkasına ait sistemi taramaması için `.env` dosyasında `REQUIRE_TARGET_VERIFICATION=true` yapın. Bu durumda yalnızca sahipliği kanıtlanmış hedefler (ve herkese açık test sunucusu `scanme.nmap.org`) taranabilir. **Abonelik → Doğrulanmış hedefler** bölümünden hedef ekleyin ve size verilen anahtarı iki yoldan biriyle yayınlayın:

| Yöntem | Yapılacak |
|--------|-----------|
| **DNS** | Alan adına `TXT` kaydı: `reconclaw-verify=<anahtar>` |
| **Dosya** | `https://<hedef>/.well-known/reconclaw-verify.txt` adresine anahtarı içeren dosya |

Ardından **DOĞRULA**'ya basın. DNS sorgusu DNS-over-HTTPS ile yapılır; iç ağ adresleri `ALLOW_PRIVATE_TARGETS=false` iken doğrulanamaz (SSRF koruması).

---

## ⚙️ Nasıl Çalışır?

Bir tarama isteği, arka planda şu yolu izler:

```mermaid
flowchart LR
    A[🧑‍💻 Hedef<br>scanme.nmap.org] --> B[Girdi temizleme<br>normalize_target]
    B --> C[DNS çözümleme]
    C --> D{İç ağ adresi?<br>ALLOW_PRIVATE_TARGETS}
    D -- engelli --> X[403 Reddedildi]
    D -- izinli --> E[Asenkron TCP taraması<br>en fazla 300 eşzamanlı bağlantı]
    E --> F[Banner yakalama<br>HTTP portlarında HEAD isteği]
    F --> G[Eklentiler<br>HTTP başlıkları · TLS sertifikası]
    G --> H[RiskAnalyzer<br>ağırlık + CVE + bulgu puanı]
    H --> I[(SQLite<br>scans · open_ports · findings)]
    I --> K[🧠 Cortex<br>Karne · ATT&CK · Uyum]
    K --> L[🤖 AI Analist<br>Claude / kural tabanlı]
    K --> J[📊 Panel · PDF · paylaşım · CSV · JSON]
    L --> J
    M[⏱️ Zamanlayıcı<br>sürekli izleme] -. aynı tarama hattı .-> B
    I -. önceki tarama ile fark .-> N[🔔 Alarm · webhook]
```

1. **Girdi temizleme:** `https://site.com:8080/yol` → `site.com`. Geçersiz ana bilgisayar adları 422 ile reddedilir.
2. **DNS:** Alan adı IPv4 adresine çözülür; çözülemezse 400 döner.
3. **İç ağ kontrolü:** Sunucu internete açıksa `ALLOW_PRIVATE_TARGETS=false` ile 127.0.0.1, 10.x, 192.168.x gibi adresler engellenir.
4. **Tarama:** Her port için `asyncio.open_connection` ile TCP bağlantısı denenir. Semafor, aynı anda en fazla 300 bağlantıya izin verir; böylece hem hızlı olur hem de hedef boğulmaz.
5. **Banner:** Açık porttan gelen ilk satır okunur. HTTP portlarında `HEAD /` gönderilip `Server:` başlığı alınır.
6. **Eklentiler:** Yalnızca ilgilendikleri açık portlarda, eşzamanlı çalışırlar. Biri hata verirse tarama bozulmaz.
7. **Risk analizi:** Servis ağırlıkları, CVE imza puanları ve eklenti bulgu puanları toplanır (en fazla 100). Öneriler üretilir.
8. **Kayıt:** Rapor, sahibi olan kullanıcıyla birlikte SQLite'a yazılır. Panel, istatistikleri bu kayıtlardan hesaplar.
9. **Cortex (v8):** Rapor açıldığında güvenlik karnesi, ATT&CK eşlemesi ve uyum değerlendirmesi kayıtlı rapordan hesaplanır; böylece eski taramalar da yeni analizlerden yararlanır.
10. **İzleme (v7):** Zamanlayıcı aynı tarama hattını (kota, hedef doğrulama ve iç ağ kontrolleri dahil) kullanır ve sonucu bir önceki taramayla karşılaştırıp alarm üretir.

<details>
<summary><b>🔐 Sosyal giriş (OAuth) akışı</b></summary>

```mermaid
sequenceDiagram
    participant K as Kullanıcı
    participant R as ReconClaw
    participant S as Sağlayıcı (Google/GitHub/...)
    K->>R: /auth/google/login
    R->>R: Tek kullanımlık state + PKCE doğrulayıcısı (DB, 10 dk)
    R-->>K: Sağlayıcının onay ekranına yönlendir
    K->>S: Hesabı seç, izin ver
    S-->>K: /auth/google/callback?code=...&state=...
    K->>R: callback
    R->>R: state'i doğrula ve sil (CSRF koruması)
    R->>S: code → erişim anahtarı (sunucudan sunucuya)
    S-->>R: profil + e-posta (+ doğrulandı mı?)
    R->>R: Hesabı bul / bağla / oluştur
    R-->>K: HttpOnly oturum çerezi, panele yönlendir
```

Sosyal hesap, var olan bir e-posta hesabına **yalnızca sağlayıcı e-postayı doğrulamışsa** bağlanır. Böylece başkası aynı e-postayı yazarak hesabınızı ele geçiremez.
</details>

---

## 📊 Risk Değerlendirme Modeli

Her açık port, servisin kritikliğine göre bir **risk ağırlığı** taşır. Portun kendi riski `ağırlık × 2` (en fazla %100), hedefin toplam skoru ise tüm ağırlıkların toplamıdır (en fazla 100).

| Ağırlık | Servisler |
|:-------:|-----------|
| **25** | Telnet (23), SMB (445), MSSQL (1433), Oracle (1521), MySQL (3306), PostgreSQL (5432), Redis (6379), Elasticsearch (9200), MongoDB (27017) |
| **20** | NetBIOS (139), NFS (2049), RDP (3389), VNC (5900) |
| **15** | FTP (21), RPCbind (111), MS-RPC (135) |
| **10** | SSH (22), POP3 (110), IMAP (143), HTTP-Proxy (8080) |
| **5–8** | SMTP (25) 8 · DNS (53) 5 · HTTP (80) 5 · HTTPS-Alt (8443) 5 |
| **2–3** | HTTPS (443) 2 · IMAPS (993) 3 · POP3S (995) 3 · bilinmeyen port 3 |

**Ek puanlar:**

| Kaynak | Puan |
|--------|------|
| CVE imzası eşleşmesi | +25 … +50 (aşağıdaki tablo) |
| Eklenti bulgusu | Yüksek +15 · Orta +8 · Düşük +3 · Bilgi 0 |

| Risk Seviyesi  | Skor         | Durum     | Açıklama                                                                  |
| :------------- | :----------: | :-------: | ------------------------------------------------------------------------- |
| 🟢 Düşük Risk  | **0 – 25**   | Güvenli   | Kritik seviyede bir güvenlik riski bulunmamaktadır.                       |
| 🟡 Orta Risk   | **26 – 50**  | İzlenmeli | Yapılandırma iyileştirmeleri ve düzenli kontroller önerilir.              |
| 🟠 Yüksek Risk | **51 – 75**  | Riskli    | Açık servisler saldırı yüzeyini artırıyor; önlemler güçlendirilmelidir.   |
| 🔴 Kritik Risk | **76 – 100** | Kritik    | Kritik servisler veya bilinen zafiyetler tespit edildi; acil aksiyon alın. |

**Tanınan CVE imzaları:**

| Banner İmzası          | Zafiyet                                                | Ek puan |
| ---------------------- | ------------------------------------------------------ | :-----: |
| vsFTPd 2.3.4           | CVE-2011-2523 (arka kapı)                              | +50 |
| Apache 2.4.49 / 2.4.50 | CVE-2021-41773 / CVE-2021-42013 (Path Traversal & RCE) | +50 |
| OpenSSH 4.x – 6.x      | CVE-2016-10009 ve benzeri eski sürüm açıkları          | +30 |
| ProFTPD 1.3.0 – 1.3.5  | CVE-2015-3306 (mod_copy)                               | +30 |
| Microsoft-IIS 5 – 7    | Desteği bitmiş sürüm                                   | +25 |

**Örnek hesap:** `22/SSH (OpenSSH_5.3)` + `80/HTTP` + `3306/MySQL` açık bir hedef için → SSH 10 + CVE 30 + HTTP 5 + MySQL 25 = **70 → 🟠 Yüksek Risk**.

> **Not:** Risk skoru hızlı bir **ön değerlendirmedir**; kapsamlı bir sızma testinin veya zafiyet taramasının yerini tutmaz.

---

## 🧩 Eklentiler

Port taraması bittikten sonra eklentiler, ilgilendikleri açık portlarda ek kontroller yapar. Bulguların şiddetine göre (Yüksek +15, Orta +8, Düşük +3, Bilgi 0) ilgili portun ve hedefin risk skoru artar.

| Eklenti        | Portlar                          | Kontroller                                                                 |
|
---

## 🔌 API

Etkileşimli API dokümantasyonu (Swagger): **http://127.0.0.1:8000/docs**

Tüm `/api/*` uç noktaları oturum ister. API anahtarı **Pro Max** ve üzeri planlarda kullanılabilir. Tarayıcıda giriş çerezi kullanılır; script ve curl için **Ayarlar → API erişimi**'nden oluşturulan anahtar `Authorization: Bearer rc_...` başlığıyla gönderilir.

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
### Tüm uç noktalar

| Uç Nokta | Açıklama |
| -------- | -------- |
| `POST /api/scan` | Tarama başlat, tam raporu döndür |
| `GET /api/history?limit=20&q=` | Son taramaların özet listesi (`q` ile hedef/IP araması) |
| `GET /api/scans/{id}` | Kayıtlı bir taramanın tam raporu |
| `DELETE /api/scans/{id}` · `DELETE /api/scans` | Bir taramayı / tüm geçmişi sil |
| `GET /api/scans/{id}/csv` | Raporu CSV olarak indir (Excel formül enjeksiyonuna karşı temizlenmiş) |
| `GET /reports/{id}` | Yazdırılabilir / PDF'e kaydedilebilir rapor sayfası |
| `GET /api/compare?old=1&new=2` | İki tarama arasındaki fark |
| `GET /api/stats` | Panel istatistikleri, trend, olay kaydı, aktivite takvimi |
| `GET /api/plugins` | Eklentiler, çalıştıkları portlar ve etkin olup olmadıkları |
| `GET /api/me` · `PATCH /api/me` · `DELETE /api/me` | Profil bilgisi, ad güncelleme, hesabı silme |
| `POST /api/me/password` | Parola değiştir / belirle (diğer oturumları kapatır) |
| `POST /api/me/token` · `DELETE /api/me/token` | API anahtarı oluştur / iptal et |
| `POST /api/me/sessions/revoke` | Diğer cihazlardaki oturumları kapat |
| `POST /auth/register` · `POST /auth/login` · `POST /auth/logout` | E-posta ile kayıt, giriş, çıkış |
| `GET /auth/providers` | Hangi sosyal giriş yöntemlerinin açık olduğu |
| `GET /auth/{google\|github\|microsoft\|apple}/login` | Sosyal giriş |
| `GET /api/plans` | Plan kataloğu ve fiyatlar (oturum gerektirmez) |
| `GET /api/billing` | Mevcut plan, bitiş tarihi, bugünkü kullanım ve ödeme geçmişi |
| `POST /api/billing/checkout` | `{"plan": "pro", "period": "monthly\|yearly"}` ile plana geç (demo ödeme) |
| `POST /api/billing/cancel` | Aboneliği iptal et, Free plana dön |
| `GET /api/targets` · `POST /api/targets` | Doğrulama hedeflerini listele / ekle |
| `POST /api/targets/{id}/verify` · `DELETE /api/targets/{id}` | Hedefi DNS veya dosya ile doğrula / sil |
| `GET /api/scans/{id}/intel` | **v8:** Güvenlik karnesi, MITRE ATT&CK eşlemesi ve uyum ön değerlendirmesi |
| `GET /api/scans/{id}/ai` · `POST /api/scans/{id}/ai` | **v8:** AI Analist notları / `{"question": "..."}` ile soru veya `{}` ile rapor değerlendirmesi |
| `GET` · `POST` · `DELETE /api/scans/{id}/share` | **v8:** Salt-okunur paylaşım bağlantısı durumu / oluştur / iptal et |
| `GET /share/{anahtar}` | **v8:** Paylaşılan rapor sayfası (oturum gerektirmez) |
| `GET /api/monitors` · `POST /api/monitors` | **v7:** İzleme görevleri / `{"target", "interval": "hourly\|daily\|weekly", "max_port", "webhook"}` |
| `PATCH /api/monitors/{id}` · `POST /api/monitors/{id}/run` · `DELETE /api/monitors/{id}` | **v7:** Görevi duraklat/başlat, hemen çalıştır, sil |
| `GET /api/alerts` · `POST /api/alerts/seen` | **v7:** İzleme alarmları / tümünü okundu işaretle |
| `POST /api/recon` · `GET /api/recon` · `GET /api/recon/{id}` | **v7:** Pasif keşif başlat `{"domain"}` / geçmiş / kayıtlı sonuç |
| `GET /api/me/audit` | **v7:** Hesabınızın güvenlik olayları |
| `GET /api/admin/overview` · `GET /api/admin/users` · `GET /api/admin/audit` | **v7 (yönetici):** Sistem özeti, kullanıcı listesi, denetim kaydı |
| `PATCH /api/admin/users/{id}` · `DELETE /api/admin/users/{id}` | **v7 (yönetici):** `{"role", "plan", "days", "disabled"}` ile güncelle / sil |
| `GET /api/health` | Sağlık kontrolü (oturum gerektirmez) |

<details>
<summary><b>🐍 Python ile kullanım örneği</b></summary>

```python
import httpx

API = "http://127.0.0.1:8000"
HEADERS = {"Authorization": "Bearer rc_ANAHTARINIZ"}

rapor = httpx.post(f"{API}/api/scan", headers=HEADERS,
                   json={"target": "scanme.nmap.org"}, timeout=120).json()

print(f"{rapor['target']} → risk %{rapor['overall_risk']} ({rapor['risk_level']['label']})")
for port in rapor["analysis"]:
    print(f"  {port['port']}/tcp  {port['service']:<12} {port['banner']}")
for uyari in rapor["cve_alerts"]:
    print("  ⚠", uyari)
```
</details>

---

## 🛠️ Yapılandırma (.env)

Tüm ayarlar ortam değişkenleri veya proje kökündeki `.env` dosyasıyla yapılır (`cp .env.example .env`). Gerçek ortam değişkenleri `.env`'den önceliklidir.

| Değişken | Varsayılan | Açıklama |
|----------|:----------:|----------|
| `PUBLIC_URL` | *(boş)* | Sitenin dış adresi, ör. `https://reconclaw.alanadiniz.com`. OAuth yönlendirmeleri buradan üretilir |
| `DOMAIN` | `localhost` | Docker/Caddy için alan adı (otomatik HTTPS sertifikası) |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | `python main.py` ile çalışırken dinlenen adres |
| `COOKIE_SECURE` | `PUBLIC_URL` https ise açık | Oturum çerezi yalnızca HTTPS üzerinden gönderilir |
| `SESSION_DAYS` | `7` | "Beni hatırla" ile açılan oturumun ömrü (gün) |
| `ALLOW_SIGNUP` | `true` | Yeni kayıtlara izin ver. Kendi hesabınızı açtıktan sonra kapatabilirsiniz |
| `ALLOW_PRIVATE_TARGETS` | `true` | İç ağ adreslerinin taranması. **İnternete açık sunucuda `false` yapın** |
| `SCAN_RATE_LIMIT` | `0` | Plan sınırlarına ek, tüm kullanıcılar için dakikalık üst sınır (0 = kapalı, yalnızca plan sınırları) |
| `REQUIRE_TARGET_VERIFICATION` | `false` | Yalnızca sahipliği doğrulanmış hedefler taransın. **Herkese açık sunucuda `true` yapın** |
| `ADMIN_EMAILS` | *(boş)* | Virgülle ayrılmış yönetici e-postaları (bkz. [Yönetim Paneli](#-yönetim-paneli-ve-admin-hesabı)) |
| `SCHEDULER_ENABLED` | `true` | Sürekli izleme zamanlayıcısı |
| `ANTHROPIC_API_KEY` | *(boş)* | AI Analist için Claude API anahtarı. Boşsa kural tabanlı analist çalışır |
| `AI_MODEL` | `claude-opus-5-5` | AI Analist'in kullandığı Claude modeli |
| `REGIONAL_SURCHARGE_TRY` | `950` | Yurt dışı fiyatlarına eklenen TL tutarı (aylık, plan başına) |
| `DEFAULT_COUNTRY` | `TR` | Ülke bulunamazsa kullanılacak ülke |
| `GEO_LOOKUP` | `true` | Ziyaretçi IP'sinin ülkesini ipapi.co ile bul |
| `TRUST_COUNTRY_HEADER` | `false` | Cloudflare `CF-IPCountry` başlığına güven |
| `FX_RATES` | *(boş)* | Kurları sabitle, ör. `USD=45,EUR=52,SAR=12` (1 birim = kaç TL) |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | *(boş)* | Cloudflare Turnstile bot doğrulaması (ikisi de doluysa giriş/kayıtta zorunlu) |
| `RECONCLAW_DB` | `data/reconclaw_v4.db` | Veritabanı dosyasının yolu |
| `GOOGLE_CLIENT_ID` / `_SECRET` | — | Google ile giriş |
| `GITHUB_CLIENT_ID` / `_SECRET` | — | GitHub ile giriş |
| `MICROSOFT_CLIENT_ID` / `_SECRET` | — | Microsoft ile giriş |
| `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY_PATH` | — | Apple ile giriş (.p8 anahtarı) |

> [!CAUTION]
> `.env` dosyası gizli anahtarlar içerir. **Asla GitHub'a yüklemeyin**; `.gitignore`'da zaten engellenmiştir.

---

## 🌐 Alan Adında Yayınlama (HTTPS)

Bir alan adı (ör. `alanadiniz.com`) ve bir sunucu (VPS) aldığınızda ReconClaw'ı tek komutla HTTPS üzerinden yayınlayabilirsiniz. [Caddy](https://caddyserver.com), Let's Encrypt'ten **ücretsiz SSL sertifikasını otomatik** alır ve yeniler.

```mermaid
flowchart LR
    U[🌍 Ziyaretçi] -- HTTPS :443 --> C[Caddy<br>otomatik sertifika]
    C -- HTTP :8000 --> A[ReconClaw<br>uvicorn]
    A --- V[(reconclaw-data<br>SQLite birimi)]
```

```bash
# 1) DNS: alan adınızın (veya reconclaw.alanadiniz.com alt alanının) A kaydını sunucunun IP'sine yönlendirin
# 2) Sunucuda (Docker kurulu değilse: curl -fsSL https://get.docker.com | sh)
git clone https://github.com/Pireburak/ReconClaw.git && cd ReconClaw
cp .env.example .env
nano .env        # DOMAIN=reconclaw.alanadiniz.com
                 # PUBLIC_URL=https://reconclaw.alanadiniz.com
                 # ALLOW_PRIVATE_TARGETS=false   <- internete açık sunucuda mutlaka
docker compose up -d --build
```

Site birkaç dakika içinde `https://reconclaw.alanadiniz.com` adresinde açılır. İlk hesabınızı oluşturduktan sonra yabancıların kayıt olmasını istemiyorsanız `.env` içinde `ALLOW_SIGNUP=false` yapıp `docker compose up -d` ile yeniden başlatın.

> [!TIP]
> Öğrenciyseniz **GitHub Student Developer Pack** ile ücretsiz alan adı ve bulut sunucu kredisi alabilirsiniz.

### 🔐 Sosyal girişi açmak

Her sağlayıcıda bir "OAuth uygulaması" oluşturup verilen ID/secret değerlerini `.env` dosyasına yazmanız yeterli. Doldurulmayan sağlayıcıların butonu pasif görünür.

| Sağlayıcı | Nereden alınır | Yönlendirme (callback) adresi | `.env` |
|-----------|----------------|-------------------------------|--------|
| Google    | [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) → *OAuth client ID (Web)* | `https://ALANADI/auth/google/callback` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |
| GitHub    | [GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers) | `https://ALANADI/auth/github/callback` | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Microsoft | [Microsoft Entra → App registrations](https://entra.microsoft.com) (*Web* platformu) | `https://ALANADI/auth/microsoft/callback` | `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` |
| Apple     | [Apple Developer](https://developer.apple.com/account/resources) → *Services ID* + *Sign in with Apple* anahtarı (.p8). Ücretli geliştirici hesabı gerekir | `https://ALANADI/auth/apple/callback` | `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY_PATH` |

> 💡 Google ve GitHub, yerel geliştirmede `http://127.0.0.1:8000/auth/.../callback` adresini de kabul eder; alan adı almadan önce deneyebilirsiniz. Apple yalnızca HTTPS alan adlarıyla çalışır.

---

## 🛡️ Güvenlik

ReconClaw bir güvenlik aracı olduğu için kendi güvenliğine de özen gösterir:

| Alan | Önlem |
|------|-------|
| **Parolalar** | Tuzlu **scrypt** ile saklanır; düz metin asla veritabanına yazılmaz. Kullanıcı olmasa bile aynı sürede yanıt verilir (zamanlama saldırısı koruması) |
| **Oturumlar** | Rastgele anahtar, veritabanında yalnızca **SHA-256 özeti**; çerez `HttpOnly` + `SameSite=Lax` (+ HTTPS'te `Secure`). Parola değişince diğer cihazlardaki oturumlar kapanır |
| **API anahtarı** | `rc_` önekli, yalnızca bir kez gösterilir, veritabanında özeti tutulur, tek tıkla iptal edilir |
| **OAuth** | Tek kullanımlık `state` (CSRF), Google/Microsoft için **PKCE**; doğrulanmamış e-posta mevcut hesaba bağlanmaz |
| **Bot koruması** *(v8.2)* | Giriş ve kayıtta isteğe bağlı **Cloudflare Turnstile** (sunucu tarafında doğrulanır) ve her zaman açık **bal küpü** gizli alanı |
| **Kötüye kullanım** | Giriş denemeleri IP başına 10 / 5 dk, taramalar kullanıcı başına `SCAN_RATE_LIMIT` / dk ile sınırlı |
| **SSRF / iç ağ** | `ALLOW_PRIVATE_TARGETS=false` ile ziyaretçilerin sunucunuzun iç ağını taraması engellenir |
| **Veri izolasyonu** | Her kullanıcı yalnızca kendi taramalarını görür, siler ve karşılaştırır |
| **HTTP başlıkları** | CSP (yalnızca `'self'`), HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy. ReconClaw kendi `http_headers` eklentisinden **temiz geçer** |
| **Dışa aktarım** | CSV'de Excel formül enjeksiyonuna karşı hücreler temizlenir; arayüzde tüm sunucu verisi HTML'e basılmadan kaçışlanır (XSS) |
| **Bağımsızlık** | Yazı tipleri projeye gömülüdür (`static/fonts`); harici CDN'e istek atılmaz |
| **Yönetici rolü** *(v7)* | Kayıt anında yöneticilik yalnızca e-postası doğrulanmış sosyal girişe verilir; yönetici kendini askıya alamaz / silemez; askıya alınan hesabın tüm oturumları ve API anahtarı anında düşer |
| **Denetim kaydı** *(v7)* | Giriş, hatalı giriş, plan, API anahtarı ve yönetici eylemleri IP ile kayıt altına alınır |
| **İstem enjeksiyonu** *(v8)* | Taranan sunucudan gelen banner'lar AI modeline ayrı veri bloğunda ve "güvenilmez veri" olarak verilir; analist savunma odaklı talimatla sınırlıdır |
| **Paylaşım** *(v8)* | 192 bit rastgele anahtar, `noindex`, `no-referrer`, tek tıkla iptal; sahibinin planı düşerse veya hesabı askıya alınırsa bağlantı çalışmaz |
| **Webhook** *(v7)* | Yalnızca http(s); `ALLOW_PRIVATE_TARGETS=false` iken iç ağ adreslerine gönderim engellenir; arayüzde adresin gizli kısmı maskelenir |

---

## 🦝 Neden Rakun?

<img src="static/img/logo.png" alt="ReconClaw rakun logosu" width="160" align="right">

> **Kısa cevap:** Keşif (*recon*) işi; gizlice yaklaşmayı, her kapıyı tek tek yoklamayı, bulduğunu hatırlamayı ve karanlıkta çalışmayı ister. Doğada bunları rakundan iyi yapan pek yoktur. Adımızdaki **Claw** (pençe) de ona ait. 🐾

ReconClaw'ın maskotu v6.0 ile **kartaldan rakuna** geçti. "Neden rakun?" diye soranlar için hikâyenin tamamı aşağıda.

### 🦅 ➜ 🦝 Kartaldan rakuna: neden değiştik?

Kartal gökyüzünden, uzaktan bakar. Bu da **pasif** keşfe (OSINT, arama motorları) daha çok benzer. ReconClaw ise **aktif** bir araç: hedefe gider, her porta TCP bağlantısı açar, kapıyı çalar, dönen banner'ı okur. Yani yukarıdan izlemek yerine yere inip **eliyle yoklayan** bir hayvan gerekiyordu. İşte o hayvan rakun.

### 🔬 Rakun hakkında gerçek bilgiler ve ReconClaw'daki karşılıkları

| Rakunun gerçek özelliği | ReconClaw'daki karşılığı |
|-------------------------|--------------------------|
| 🎭 **Doğuştan maskeli.** Gözlerinin etrafındaki siyah "maske" ışık parlamasını azaltıp gece görüşüne yardım ettiği düşünülüyor. | Hedefi yormadan, sessiz ve hızlı tarar: *recon* işi gizlilik ister. |
| 🐾 **Olağanüstü hassas ön pençeler.** Beyninin duyusal bölgesinin yaklaşık üçte ikisi dokunma algısına ayrılmıştır; bir nesneye bakmadan, sadece dokunarak tanıyabilir. | Her portu tek tek "elle yoklar", banner'ı yakalar ve servisi/sürümü tanır. Adındaki **Claw** buradan geliyor. |
| 🔐 **Kilit açma ustası.** 1900'lerin başındaki klasik bir deneyde rakunlar 13 karmaşık kilidin 11'ini on denemeden az sürede açmıştır. | Kilitli kapıları değil, **açık bırakılmış** olanları bulur ve raporlar. Kırmaz, yalnızca gösterir. |
| 🧠 **Güçlü hafıza.** Öğrendiği bir problemin çözümünü yıllarca hatırlayabildiği gözlemlenmiştir. | Her tarama SQLite'a kaydedilir. **Tarama karşılaştırma** ile neyin değiştiğini hatırlar. |
| 🔍 **Aşırı meraklı.** Her deliğe, her kutuya bakar. | Açık servisin sürümünü kurcalar, **CVE imzalarıyla** eşleştirir. Eklentiler HTTP başlıklarına ve TLS sertifikalarına da bakar. |
| 🌙 **Gece hayvanı.** | Karanlık temada kendini evinde hisseder. 🌗 |
| 🏙️ **Her ortama uyum sağlar.** Ormanda da, şehrin ortasında da yaşar. | Tek bir IP'de de, alan adında da, Docker + HTTPS ile sunucuda da çalışır. |
| 🧼 **"Yıkayıcı" rakun.** Bilimsel adı *Procyon lotor*'daki *lotor*, Latincede "yıkayan" demektir; yiyeceğini suda evirip çevirir. | Bulduğu her açık için **temizlik önerisi** üretir: servisi kapat, sürümü güncelle, IP filtresi uygula. |

### 🎨 Logonun anatomisi

| Öğe | Anlamı |
|-----|--------|
| 🟠 **Kehribar gözler** | Uyanık, her şeyi gören tarayıcı. Tarama sırasındaki radar ekranına gönderme. |
| 🦾 **Mekanik pençe** | *Claw*: portlara dokunan, banner yakalayan tarama motoru |
| ⚙️ **Dişliler** | Asenkron motor, eklenti sistemi ve birlikte dönen modüller |
| 🔥 **Alev kuyruk** | Hız: yüzlerce port saniyeler içinde |
| 🛡️ **Süslü kalkan çerçeve** | Savunma odaklı amaç. Araç saldırmak için değil, **korumak** için. |
| 🟧 **Turuncu–altın–siyah palet** | Arayüzdeki risk renkleri gibi dikkat çeker ve uyarır |

### 📍 Rakunu nerede görürsünüz?

- Panelin sol üst köşesinde (logo)
- Giriş / kayıt ekranında
- PDF raporların başlığında
- Tarayıcı sekmesinde (favicon) ve iPhone/iPad ana ekranında (apple-touch-icon)
- Sunucu açılırken konsolda: `🦝 ReconClaw v6.1 Aurora -> http://127.0.0.1:8000`

### 💬 Birisi "Neden rakun?" diye sorarsa

> *"Çünkü rakun maskelidir, meraklıdır, eline geçen her kapıyı yoklar ve bulduğunu unutmaz. Biz de öyle bir tarayıcı yaptık. Tek farkı: bizimki kapıyı açmaz, açık kaldığını söyler."* 🦝
---

## 📜 Sürüm Geçmişi

### 🛡️ v8.2 Cortex *(mevcut sürüm)*

| Özellik | Açıklama |
|---------|----------|
| Gizli yönetim paneli | Yönetici olmayanlara 404, API belgesinde ve herkese açık kodda iz yok |
| Bot koruması | Cloudflare Turnstile (isteğe bağlı) + bal küpü alanı + hız sınırı |

### 🌍 v8.1 Cortex

| Özellik | Açıklama |
|---------|----------|
| Bölgesel fiyatlandırma | IP'ye göre ülke ve para birimi (€, $, £, SAR, AED...), canlı kur, yurt dışına ≈950 TL fark; Türkiye en ucuz |

### 🧠 v8.0 Cortex

| Özellik | Açıklama |
|---------|----------|
| 🎯 MITRE ATT&CK | 14 taktiklik matris, teknik gerekçeleri, attack.mitre.org bağlantıları ve otomatik saldırı zinciri |
| 🅰️ Güvenlik karnesi | 5 kategori, A+…F not, kritik sorunlarda not tavanı |
| ⚖️ Uyum | ISO/IEC 27001:2022 Ek A (8 kontrol) + KVKK m.12 ön değerlendirmesi |
| 🤖 AI Analist | Claude (`anthropic` SDK, sunucu taraflı yedek model) veya çevrimdışı kural tabanlı analist; soru-cevap, önbellek, günlük kota |
| 🔗 Paylaşım | Salt-okunur rapor bağlantısı; PDF rapora karne, ATT&CK ve uyum bölümleri |

### 🛰️ v7.0 Sentinel

| Özellik | Açıklama |
|---------|----------|
| 👑 Yönetici rolü | `ADMIN_EMAILS` / `manage.py make-admin`; sınırsız Admin seviyesi; Ultra Max ₺1.999 ve sınırlı |
| 🗂️ Yönetim paneli | Kullanıcılar, plan atama, askıya alma, MRR, 14 günlük grafik, denetim kaydı |
| 📡 Sürekli izleme | Saatlik / günlük / haftalık zamanlanmış tarama, değişim alarmı, Discord / Slack webhook |
| 🛰️ Pasif keşif | Sertifika Şeffaflığı alt alan adları, DNS kayıtları, SPF / DMARC / CAA puanı |
| 📝 Hesap etkinliği | Kullanıcının kendi güvenlik kaydı; zilde izleme alarmları |

### 💳 v6.1 Aurora

| Özellik | Açıklama |
|---------|----------|
| 5 kademeli abonelik | Free, Pro (₺299), Pro Max (₺599), Ultra (₺999), Ultra Max (₺1.999); yıllık ödemede 2 ay bedava |
| Sunucu taraflı sınırlar | Günlük/dakikalık tarama, port aralığı, eklenti, rapor, karşılaştırma ve API kilidi (`HTTP 402`) |
| Demo ödeme | Kart bilgisi olmadan plan geçişi ve ödeme geçmişi; gerçek ödeme altyapısına hazır |
| Hedef doğrulama | DNS TXT veya `.well-known` dosyası ile sahiplik kanıtı (`REQUIRE_TARGET_VERIFICATION`) |

### 🌠 v6.0 Aurora

Tarama motoru ve API aynı kaldı; v6.0 baştan sona bir **arayüz** sürümüdür.

| Özellik | Açıklama |
|---------|----------|
| 🗂️ **"Gizli dosya" arayüzü** | İstihbarat dosyası estetiği: grafit zemin ve kâğıt beyazı yazı, vizör köşeli ince paneller, numaralı bölüm başlıkları, kırmızı **GİZLİ** sınıflandırma bandı, film greni. Neon parlama, renkli gradyan ve emoji yok |
| 📄 **Kâğıt tema** | Aydınlık tema, sararmış bir kâğıt dosya gibi |
| 🗺️ **Erişim terminali** | Dosya künyeli, sekmeli yetenek özetli, GİZLİ damgalı giriş ekranı; WebGL topoğrafik harita arka planı |
| ⌘ **Komut paleti** | Ctrl+K ile bölümler, komutlar, raporlar ve hedefler |
| ⌨️ **Klavye kısayolları** | `0`–`6`, `N`, `T`, `/`, `?`, `Esc` |
| 🧲 **İkon rayı** | Sol tarafta yalnızca ikonlardan oluşan ince menü; fare yaklaştıkça ikonlar hafifçe büyür (dock etkisi), telefonda alt bara dönüşür |
| 🎨 **5 vurgu rengi** | Mürekkep, bakır, sinyal kırmızısı, haki, çelik mavisi |
| 📊 **Canlı kartlar** | Sayan rakamlar, sparkline'lar, iskelet yükleme |
| 🗓️ **Operasyon takvimi** | Son 1 yılın gün gün tarama yoğunluğu |
| 🔔 **Bildirim zili** | Görülmemiş kritik/yüksek olaylar |
| 📡 **Radar tarama ekranı** | Dönen radar, geçen süre, risk renginde port noktaları |
| 🎯 **Yeni risk göstergesi** | 270°'lik yay; port tablosunda risk çubukları; bulgu filtreleri; IP kopyalama |
| 🕸️ **Etkileşimli ağ krokisi** | Odak modu ve port detay paneli |
| 🧭 **Yetenek özeti** | Genel bakışta sekmeli kompakt tanıtım |
| 🖨️ **Gizli dosya raporu** | GİZLİ damgalı, bantlı, dosya numaralı PDF |
| 🦝 **Rakun maskotu** | Kartal yerine rakun: logo, favicon, rapor başlığı, README banner'ı |
| 🔤 **Gömülü yazı tipleri** | IBM Plex Mono, Barlow Condensed, Courier Prime (OFL); internetsiz de aynı görünüm |
| ♻️ **Önbellek koruması** | Statik dosya adreslerine sürüm etiketi (`?v=`) eklenir; güncellemeden sonra tarayıcı eski CSS'i kullanmaz |

<details>
<summary><b>✨ v5.0 Nebula</b></summary>

| # | Özellik | Açıklama |
|---|---------|----------|
| 1 | 🛰️ **Operasyon paneli** | İstatistik kartları, tehdit halkaları, canlı olay akışı, trend ve port grafikleri, hedef risk tablosu, UTC saati ve çalışma süresi |
| 2 | 🌗 **Aydınlık / karanlık tema** | Anında geçiş; *Karanlık / Aydınlık / Sistem* seçimi |
| 3 | 🔐 **Kullanıcı girişi** | E-posta + parola (scrypt), Google / GitHub / Microsoft / Apple (OAuth 2.0 / OpenID Connect). Herkes yalnızca kendi taramalarını görür |
| 4 | ⇄ **Tarama karşılaştırma** | Açılan / kapanan portlar, sürümü değişen servisler, yeni / çözülen bulgular, risk değişimi |
| 5 | ◎ **Ağ haritası** | Hedef ve açık servislerin riske göre renklenen topolojisi |
| 6 | 🖨️ **PDF & CSV rapor** | Yönetici özetli yazdırılabilir rapor ve CSV |
| 7 | 🔑 **API anahtarı & hesap güvenliği** | Kişisel API anahtarı, parola değiştirme, diğer cihazlardan çıkış, geçmişi/hesabı silme |
| 8 | 🌐 **Alan adında yayın** | Docker + Caddy ile otomatik HTTPS; iç ağ engeli, hız sınırı, güvenlik başlıkları |
</details>

<details>
<summary><b>🚀 v4.0 Phantom ve öncesi</b></summary>

**v4.0 Phantom**
- Modüler mimari (`core/`, `templates/`, `static/`)
- Asenkron, eşzamanlılık sınırlı tarama motoru
- Banner grabbing ve sürüm tespiti
- CVE imza uyarı sistemi ve öneri motoru
- Tarama geçmişi, geçmiş rapor görüntüleme ve JSON dışa aktarma
- Eklenti sistemi (HTTP güvenlik başlıkları, TLS sertifika analizi)

**v1.0 – v3.0**
- İlk TCP tarayıcı, JSON çıktısı, CLI
- Koyu tema, servis tanımlama, performans iyileştirmeleri
- Dashboard, FastAPI, SQLite, risk motoru, canlı terminal
</details>

---

## 📂 Proje Yapısı

```text
ReconClaw/
├── main.py                 # FastAPI uygulaması: sayfalar, API, güvenlik başlıkları, hız sınırı, zamanlayıcı
├── manage.py               # Yönetim komutları: make-admin, remove-admin, list-admins
├── core/
│   ├── config.py           # .env / ortam değişkeni ayarları
│   ├── plans.py            # Abonelik planları, kotalar, demo ödeme, Admin seviyesi
│   ├── pricing.py          # v8.1: IP'ye göre ülke, para birimi, kur ve bölgesel fiyat
│   ├── captcha.py          # v8.2: Cloudflare Turnstile + bal küpü bot koruması
│   ├── verify.py           # Hedef sahipliği doğrulama (DNS TXT / .well-known)
│   ├── admin.py            # v7: Yönetim paneli (özet, kullanıcılar, plan atama, askıya alma)
│   ├── audit.py            # v7: Denetim kaydı
│   ├── monitor.py          # v7: Sürekli izleme, değişim alarmları, webhook, zamanlayıcı
│   ├── recon.py            # v7: Pasif keşif (CT logları, DNS, SPF / DMARC / CAA)
│   ├── intel.py            # v8: MITRE ATT&CK, güvenlik karnesi, ISO 27001 / KVKK uyumu
│   ├── ai.py               # v8: AI Analist (Claude + kural tabanlı yedek)
│   ├── engine.py           # AsyncScanner (DNS + TCP + banner) ve RiskAnalyzer
│   ├── auth.py             # Kullanıcılar, scrypt, oturumlar, API anahtarı
│   ├── oauth.py            # Google / GitHub / Microsoft / Apple girişi (state + PKCE)
│   ├── insights.py         # Panel istatistikleri, aktivite takvimi, tarama karşılaştırma
│   ├── db_manager.py       # SQLite bağlantısı, tablolar, otomatik şema güncelleme
│   └── plugins/            # Eklenti sistemi
│       ├── __init__.py     #   Plugin temel sınıfı, yükleyici
│       ├── http_headers.py #   HTTP güvenlik başlıkları
│       └── tls_cert.py     #   TLS sertifikası ve protokol
├── templates/
│   ├── index.html          # Operasyon merkezi ve tüm bölümler (tek sayfa)
│   ├── login.html          # Erişim terminali (giriş / kayıt)
│   └── report.html         # GİZLİ damgalı yazdırılabilir rapor
├── static/
│   ├── css/style.css       # "Gizli dosya" arayüzü (karanlık + kâğıt tema)
│   ├── js/
│   │   ├── app.js          #   Panel mantığı, grafikler, harita, palet, kısayollar
│   │   ├── ops.js          #   v7: Pasif keşif ve sürekli izleme sayfaları
│   │   ├── admin.js        #   v7: Yönetim paneli (yalnızca yöneticilere yüklenir)
│   │   ├── intel.js        #   v8: Derin analiz paneli, AI Analist, paylaşım
│   │   ├── login.js        #   Giriş / kayıt formu
│   │   ├── theme.js        #   Tema ve vurgu rengi (erken yüklenir)
│   │   ├── fx.js           #   İkon rayı büyütme, sayaçlar, sparkline
│   │   ├── smoke.js        #   WebGL topoğrafik harita arka planı
│   │   └── report.js       #   Rapor yazdırma
│   ├── fonts/              # Gömülü yazı tipleri (OFL lisansı: fonts/OFL.txt)
│   ├── img/                # 🦝 Maskot: banner.jpg, logo.png, apple-touch-icon.png
│   └── favicon.png
├── tests/                  # 96 otomatik test (pytest)
├── docs/
│   ├── YARISMA.md          # TÜBİTAK / TEKNOFEST proje dosyası
│   └── screenshots/        # README ekran görüntüleri
├── deploy/Caddyfile        # HTTPS ters vekil ayarı
├── Dockerfile · docker-compose.yml
├── .env.example            # Tüm ayarlar (kopyalayıp .env yapın)
├── plugins                 # Etkin eklentiler listesi
├── requirements.txt
└── data/                   # reconclaw_v4.db (otomatik oluşturulur)
```

---

## 💾 Veritabanı

Uygulama ilk açılışta `data/reconclaw_v4.db` dosyasını ve tabloları otomatik oluşturur. Eski sürümlerden kalan veritabanları **veri kaybı olmadan** otomatik güncellenir; kimlik doğrulama gelmeden önce yapılmış taramalar ilk açılan hesaba aktarılır.

| Tablo        | Alanlar                                                                          |
| ------------ | -------------------------------------------------------------------------------- |
| `scans`      | `id`, `user_id`, `target`, `ip_address`, `open_count`, `risk_score`, `risk_level`, `duration`, `scan_time`, `report` (tam JSON rapor), `share_token` |
| `open_ports` | `id`, `scan_id`, `port`, `protocol`, `service`, `banner`, `risk`                 |
| `findings`   | `id`, `scan_id`, `plugin`, `port`, `severity`, `title`, `detail`                 |
| `users`      | `id`, `email`, `name`, `password_hash` (scrypt), `avatar_url`, `api_token` (SHA-256), `plan`, `plan_expires`, `role` (user/admin), `disabled`, `created_at`, `last_login` |
| `identities` | `id`, `user_id`, `provider` (google/github/…), `subject`                          |
| `sessions`   | `token_hash`, `user_id`, `created_at`, `expires_at`, `user_agent`                |
| `oauth_states` | `state`, `provider`, `verifier`, `created_at` (10 dk geçerli, tek kullanımlık) |
| `usage`      | `user_id`, `day`, `scans`, `ai` (günlük tarama ve AI sayacı)                      |
| `payments`   | `id`, `user_id`, `plan`, `period`, `amount`, `currency`, `country`, `amount_try`, `status` (`demo`), `created_at` |
| `targets`    | `id`, `user_id`, `host`, `token`, `method` (dns/file), `verified_at`, `created_at` |
| `audit_log`  | `id`, `user_id`, `actor_id`, `action`, `detail`, `ip`, `created_at` |
| `monitors`   | `id`, `user_id`, `target`, `interval`, `max_port`, `webhook`, `enabled`, `last_run`, `next_run`, `last_scan_id`, `last_status` |
| `alerts`     | `id`, `user_id`, `monitor_id`, `scan_id`, `target`, `level`, `title`, `detail`, `seen`, `created_at` |
| `recon_runs` | `id`, `user_id`, `domain`, `result` (JSON), `created_at` (kullanıcı başına son 30) |
| `ai_notes`   | `id`, `scan_id`, `user_id`, `question`, `answer`, `engine` (claude/kural), `created_at` |

---

## 🧪 Testler

```bash
pip install pytest
pytest
```

| Dosya | Test | Kapsam |
|-------|:----:|--------|
| `test_engine.py` | 18 | Hedef temizleme, asenkron tarayıcı, banner, risk motoru, CVE imzaları |
| `test_api.py` | 11 | Tarama/geçmiş/silme, kullanıcı izolasyonu, CSV, rapor, karşılaştırma, istatistik, iç ağ engeli, API anahtarı, güvenlik başlıkları, önbellek etiketi |
| `test_auth.py` | 10 | scrypt, kayıt/giriş/çıkış, doğrulama, parola değişimi, hesap silme, OAuth state ve hesap bağlama |
| `test_plugins.py` | 6 | HTTP başlık ve TLS eklentileri, eklenti yükleyici |
| `test_insights.py` | 4 | Panel istatistikleri, aktivite takvimi, tarama karşılaştırma |
| `test_plans.py` | 12 | Plan kataloğu, kota ve port sınırları, eklenti kilidi, dakikalık sınır, ödeme/iptal, süre dolumu, API kilidi, hedef doğrulama |
| `test_admin.py` | 7 | Admin seviyesi, panel erişim kontrolü, plan atama, askıya alma, kendini kilitleme koruması, denetim kaydı, `manage.py`, doğrulanmamış e-postayla yöneticilik engeli |
| `test_monitoring.py` | 9 | İzleme plan sınırları, yeni port alarmı ve webhook, plan düşünce duraklatma, zamanlayıcı, alarm kuralları, SPF / DMARC / CAA, alt alan adı etiketleri, keşif API'si |
| `test_captcha.py` | 3 | Bal küpü, Turnstile zorunluluğu ve sunucu tarafı doğrulama, varsayılan kapalı |
| `test_pricing.py` | 5 | Bölgeye göre para birimi, Türkiye'nin en ucuz olması, x,99 yuvarlama, ülke tespiti, ödemenin tespit edilen bölgeden alınması |
| `test_intel.py` | 11 | ATT&CK eşlemesi ve saldırı zinciri, karne ve not tavanı, uyum, kural tabanlı analist, Claude hatasında yedeğe düşme, istem enjeksiyonu koruması, AI kotası ve önbelleği, paylaşım bağlantısı |

---

## 🧯 Sorun Giderme

<details>
<summary><b>Güncellemeden sonra arayüz bozuk / eski görünüyor</b></summary>

Tarayıcı eski stil dosyasını önbellekte tutuyor olabilir. Sayfada **Ctrl+Shift+R** ile zorla yenileyin. v6.0 ile statik dosyalara sürüm etiketi eklendiği için bu sorun bir daha yaşanmaz. Kodu güncellediğinizden emin olun:
```bash
git checkout main && git pull origin main
```
Ardından sunucuyu yeniden başlatın (**Ctrl+C**, sonra `python main.py`).
</details>

<details>
<summary><b><code>error: externally-managed-environment</code></b></summary>

Sanal ortam etkin değildir (satır başında `(.venv)` yazmaz). Kali/Debian'da:
```bash
sudo apt install -y python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
</details>

<details>
<summary><b><code>Could not open requirements file</code></b></summary>

Komutu proje klasörünün dışında çalıştırıyorsunuz. Önce `cd ~/ReconClaw` yazın; `ls` çıktısında `main.py` ve `requirements.txt` görünmelidir.
</details>

<details>
<summary><b><code>cryptography</code> / <code>pyjwt</code> kurulum hatası</b></summary>

Bu paket yalnızca **Apple ile giriş** için gereklidir. Geri kalan her şey onsuz çalışır:
```bash
pip install fastapi "uvicorn[standard]" jinja2 pydantic httpx
```
</details>

<details>
<summary><b>Google / GitHub butonu soluk ve tıklanmıyor</b></summary>

O sağlayıcı yapılandırılmamış demektir. `.env` dosyasına `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` (veya Google karşılıklarını) yazıp sunucuyu yeniden başlatın. Adımlar: [Sosyal girişi açmak](#-sosyal-girişi-açmak).
</details>

<details>
<summary><b>Giriş ekranındaki harita yavaş / takılıyor</b></summary>

VirtualBox'ta 3D hızlandırma kapalıysa WebGL yazılımla çizilir. **Ayarlar → Ekran → 3D Hızlandırmayı Etkinleştir** seçeneğini açın. İşletim sisteminde "hareketi azalt" açıksa harita sabit kalır.
</details>

<details>
<summary><b><code>[Errno 98] Address already in use</code></b></summary>

8000 portu başka bir süreçte açık (muhtemelen önceki ReconClaw). O terminalde **Ctrl+C** yapın ya da farklı port kullanın: `PORT=8001 python main.py`.
</details>

<details>
<summary><b>YÖNETİM menüsü görünmüyor</b></summary>

Hesabınız yönetici değil. `python manage.py make-admin sizin@mailiniz.com` çalıştırın (hesabın önceden açılmış olması gerekir) ve sayfayı yenileyin. Plan rozetinde **ADMIN** yazmalıdır.
</details>

<details>
<summary><b>AI Analist "KURAL TABANLI (ÇEVRİMDIŞI)" yazıyor</b></summary>

`.env` dosyasında `ANTHROPIC_API_KEY` tanımlı değil ya da `anthropic` paketi kurulu değil. Anahtarı [console.anthropic.com](https://console.anthropic.com) adresinden alıp `.env`'e yazın, `pip install -r requirements.txt` çalıştırın ve sunucuyu yeniden başlatın. Anahtar olmadan da kural tabanlı analist çalışmaya devam eder.
</details>

<details>
<summary><b>Pasif keşif "kaynak: erişilemedi" diyor</b></summary>

crt.sh ve CertSpotter'a ulaşılamadı (internet yok, kurum güvenlik duvarı ya da servis yoğun). Birkaç dakika sonra tekrar deneyin; DNS ve e-posta değerlendirmesi için de internet erişimi gerekir.
</details>

<details>
<summary><b>Tarama 403 "İç ağ / özel adreslerin taranması kapalı" diyor</b></summary>

`.env` içinde `ALLOW_PRIVATE_TARGETS=false` ayarlı. Yerel laboratuvar için `true` yapın; internete açık sunucuda `false` kalmalıdır.
</details>

---

## 🎓 Sunum Rehberi

ReconClaw'ı 7–8 dakikada etkileyici biçimde göstermek için önerilen akış (ayrıntılı jüri dosyası: [docs/YARISMA.md](docs/YARISMA.md)):

| # | Adım | Ne söylenir? |
|---|------|--------------|
| 1 | **Erişim terminalini** açın, yönetici hesabıyla girin | "Çok kullanıcılı, OAuth destekli; plan rozetinde ADMIN görüyorsunuz" |
| 2 | `1` → `scanme.nmap.org` → **Taramayı başlat** | "Asenkron motor: yüzlerce port aynı anda, radarda canlı" |
| 3 | **Hedef dosyası** → **Derin analiz → Karne** | "Bulgular A+…F nota dönüşüyor; CVE varsa not D'yi geçemiyor" |
| 4 | **MITRE ATT&CK** sekmesi, bir tekniğe tıklayın | "Her açık port bir saldırı tekniğine bağlanıyor; keşiften etkiye olası saldırı zinciri" |
| 5 | **Uyum** sekmesi | "ISO 27001 ve KVKK m.12 açısından ön değerlendirme, kanıtıyla" |
| 6 | **AI Analist → Değerlendirme üret**, sonra bir soru sorun | "Claude Türkçe aksiyon planı üretiyor; internet yoksa kural tabanlı analist devreye giriyor. Banner'lardan gelen istem enjeksiyonuna karşı korumalı" |
| 7 | `7` → **Sürekli izleme** → görev ekle → **Şimdi tara** | "Değişiklik olduğunda alarm ve Discord bildirimi geliyor" |
| 8 | `6` → **Pasif keşif** | "Hedefe tek paket göndermeden Sertifika Şeffaflığı loglarından alt alan adları ve e-posta güvenliği" |
| 9 | **PAYLAŞ** → bağlantıyı telefonda açın | "Jüri raporu oturum açmadan görebiliyor; tek tıkla iptal" |
| 10 | `A` → **Yönetim** paneli | "Gelir, kullanıcılar, plan atama ve denetim kaydı: bir SaaS ürününün yönetim katmanı" |

**Olası sorulara hazır cevaplar:**

- *"Nmap'ten farkı ne?"* → Nmap'in yerini tutmaz; üzerine risk skoru, ATT&CK eşlemesi, uyum değerlendirmesi, AI destekli aksiyon planı, sürekli izleme ve raporlama katmanı ekleyen web tabanlı bir platformdur.
- *"Yapay zekâ uydurursa?"* → Model yalnızca rapor verisine dayanmakla ve veride olmayan CVE yazmamakla sınırlandırıldı; karne, ATT&CK ve uyum ise yapay zekâdan bağımsız, deterministik ve testli kurallarla hesaplanıyor.
- *"Banner'a 'önceki talimatları unut' yazan bir sunucu taranırsa?"* → Banner'lar modele ayrı veri bloğunda ve "güvenilmez veri" olarak veriliyor; analist savunma odaklı talimatla sınırlı.
- *"Kötüye kullanılırsa?"* → Hedef sahipliği doğrulama (DNS TXT / dosya), iç ağ engeli, plan bazlı kotalar, hız sınırı, denetim kaydı ve hesap askıya alma var. Araç yalnızca izinli hedefler içindir.
- *"Parolalar nasıl saklanıyor?"* → Tuzlu scrypt; oturum anahtarlarının ve API anahtarlarının bile yalnızca SHA-256 özeti tutuluyor.
- *"Kendi güvenliği nasıl?"* → ReconClaw kendi arayüzünü taradığında güvenlik başlıkları eksiksiz çıkıyor; 96 otomatik test her değişiklikte çalışıyor.

---

## 🛣️ Yol Haritası

**✅ Tamamlananlar (v7.0 – v8.0)**
- [x] Zamanlanmış (periyodik) taramalar ve bildirim (Discord / Slack webhook)
- [x] Yapay zekâ destekli analist (Claude) ve çevrimdışı kural tabanlı analist
- [x] MITRE ATT&CK eşleştirme, ISO 27001 / KVKK uyum ön değerlendirmesi
- [x] Pasif keşif: Sertifika Şeffaflığı, DNS, e-posta güvenliği
- [x] Yönetici paneli, denetim kaydı, salt-okunur rapor paylaşımı

**🔭 Sıradaki adımlar**
- [ ] Gerçek ödeme altyapısı (iyzico) ve e-fatura
- [ ] İki adımlı doğrulama (TOTP)
- [ ] Çoklu hedef / CIDR aralığı taraması ve UDP tarama
- [ ] CVE veritabanı entegrasyonu (NVD / OSV) ve EPSS ile istismar olasılığı
- [ ] Türkçe / İngilizce dil seçimi
- [ ] SIEM entegrasyonu (syslog / Elastic), e-posta bildirimleri

---

## ⚖️ Yasal Uyarı

ReconClaw yalnızca **sahibi olduğunuz** veya **yazılı izin aldığınız** sistemlerde, **eğitim** ve **etik güvenlik testi** amacıyla kullanılmalıdır. İzinsiz port taraması birçok ülkede (Türkiye'de TCK 243–245 kapsamında) suç teşkil edebilir. Yazılımın kötüye kullanımından doğan tüm hukuki sorumluluk kullanıcıya aittir.

Yasal test için Nmap'in resmi test sunucusu `scanme.nmap.org` veya kendi laboratuvarınızdaki makineler kullanılabilir.

---

## 🙏 Teşekkür ve Lisanslar

- Yazı tipleri: [IBM Plex Mono](https://github.com/IBM/plex), [Barlow](https://github.com/jpt/barlow), [Courier Prime](https://github.com/quoteunquoteapps/CourierPrime). Üçü de SIL Open Font License 1.1 ile lisanslıdır (`static/fonts/OFL.txt`).
- İkonlar: [Lucide](https://lucide.dev) (ISC lisansı) çizgisinde SVG ikonlar
- Test sunucusu: [scanme.nmap.org](http://scanme.nmap.org), Nmap Project
- Altyapı: [FastAPI](https://fastapi.tiangolo.com), [Uvicorn](https://www.uvicorn.org), [SQLite](https://sqlite.org), [Caddy](https://caddyserver.com)

---

## ✍️ Geliştirici

<p align="center">
<img src="static/img/logo.png" alt="ReconClaw" width="72"><br>
<b>Burak Özdemir</b> — <a href="https://github.com/Pireburak">@Pireburak</a><br>
<sub>ReconClaw'ı beğendiyseniz rakunumuza bir ⭐ bırakmayı unutmayın! 🦝</sub>
</p>
