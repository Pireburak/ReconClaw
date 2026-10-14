# Admin incelemesi — 14 Ekim 2026

## Paket atama

İncelenen yerel veritabanında tek hesap ve `owner` rolü vardı. Sahip ve yönetici
rolleri tüm paket özelliklerine sınırsız erişir. Bu hesaplara paket atama kontrolleri
bu nedenle kapalıydı. Arayüz artık nedenini açıkça gösterir. Normal üyeler için
paket ve süre atama akışı korunur; mevcut API testleri bu akışı doğrular.

Kullanıcı yönetimi artık özet, ekip, ayar veya denetim isteğinin başarısız olmasından
etkilenmez. Plan kataloğuna erişilememesi hâlâ paket seçeneklerinin yüklenmesini
engeller ve hata bildirimi gösterilir.

## Düzeltilen güvenlik sorunları

- **Yüksek — açılışta yetki yükseltme:** Herkese açık parolalı kayıt ile
  `ADMIN_EMAILS` / `OWNER_EMAIL` adresini alan kişi, yeniden başlatmada yetkili
  olabiliyordu. Yeni `email_verified` sütunu eski hesaplarda varsayılan olarak
  kapalıdır. Otomatik yükseltme yalnızca doğrulanmış, parolasız sosyal hesaplara
  uygulanır. Önceden parolayla kaydedilmiş hesaba sosyal giriş bağlamak otomatik
  yetkilendirme için yeterli değildir. Mevcut admin/sahip rolleri korunur.
  Eski sosyal hesapların doğrulama bilgisi, aynı adresin sağlayıcı tarafından
  doğrulandığı sonraki sosyal girişte güncellenir.
- **Orta — kısmi kullanıcı güncellemesi:** Geçersiz paketle birlikte rol veya
  askıya alma gönderilince hata yanıtına rağmen değişiklikler kalıyordu. Paket
  önceden doğrulanır; rol, askıya alma, oturum iptali ve paket tek işlemde kaydedilir.
- **Orta — moderatöre ödeme bilgisi sızması:** Liste yanıtında gizlenen ödeme
  toplamı, kullanıcı güncelleme yanıtında görünüyordu. Güncelleme yanıtında da gizlenir.
- **Düşük — CSRF kontrolünü atlama:** Oturum çerezi taşıyan isteğe herhangi bir
  Bearer başlığı eklenmesi kaynak kontrolünü atlatıyordu. Özellikle çıkış gibi
  doğrudan çerezi kullanan uç noktalar etkileniyordu. Çerezli değişiklik isteklerinin
  tamamı artık kaynak kontrolünden geçer.

Parolalı hesabı ilk kez yetkilendirmek için sunucuda `manage.py make-admin EPOSTA`
veya `manage.py make-owner EPOSTA` kullanılır. Ortam değişkenine adres eklemek,
doğrulanmamış parolalı hesabı artık otomatik yetkilendirmez.

## Kapsam ve kalan noktalar

İnceleme yerel kaynak kodu, geçici test veritabanları ve admin JavaScript testlerini
kapsar. Canlı sunucu veya gerçek ödeme sağlayıcısı test edilmedi. Gerçek kullanıcı
verileri ve roller değiştirilmedi. Yeni sütun uygulama yeniden başladığında eklenir.

Varsayılan yapılandırmada kayıt ve özel ağ taramaları açık, hedef doğrulaması
kapalıdır. Bu ayarlarla internete açılan sunucuda üyeler sunucunun erişebildiği özel
ağları tarayabilir. Üretim ortamının erişim politikası ayrıca değerlendirilmelidir.
Kod incelemesi projenin tüm güvenlik açıklarının giderildiği anlamına gelmez.

Mevcut veritabanının geçici kopyasında şema geçişi iki kez çalıştırıldı; kullanıcı
kimlikleri ve rollerinin korunduğu doğrulandı. Testler gerçek veritabanını değiştirmez.
