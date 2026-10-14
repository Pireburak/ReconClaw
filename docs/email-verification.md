# Şirket e-postasıyla doğrulama

SMTP bilgileriniz şirketinizin e-posta yöneticisi veya hosting panelinden alınır.
Webmail adresi her zaman SMTP sunucusu değildir. Parolayı kaynak koduna veya Git'e
eklemeyin; proje kökündeki, Git tarafından yok sayılan `.env` dosyasına yazın.

```dotenv
PUBLIC_URL=https://siteniz.com
SMTP_HOST=smtp.sirketiniz.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=guvenlik@sirketiniz.com
SMTP_PASSWORD=SIRKETIN_VERDIGI_SMTP_PAROLASI
SMTP_FROM=guvenlik@sirketiniz.com
REQUIRE_EMAIL_VERIFICATION=true
```

Sunucu ve adresler örnektir; şirketinizin gerçek değerleriyle değiştirin. Şirketiniz
465 portuyla doğrudan TLS istiyorsa `SMTP_PORT=465`, `SMTP_TLS=false` kullanın.
465 bağlantıları TLS ile açılır; `SMTP_TLS` yalnızca diğer portlardaki STARTTLS'i yönetir.
Gönderen adresi SMTP hesabının gönderim yetkisi olan bir adres olmalıdır.

Ayarları kaydettikten sonra uygulamayı yeniden başlatın. SMTP host ve gönderen
adresi tanımlıysa doğrulama varsayılan olarak açıktır; yukarıdaki açık ayar, SMTP
eksik olduğunda da doğrulamanın sessizce kapanmasını önler. SMTP kapalı ve zorunlu
doğrulama ayarı belirtilmemişse geliştirme ortamındaki eski giriş davranışı korunur.

## Kullanıcı akışı

- Kayıt olan veya giriş yapan doğrulanmamış normal kullanıcıya 6 haneli kod gönderilir.
- Kod, gönderildiği andan itibaren **15 dakika** geçerlidir ve tek kullanımlıktır.
- Kullanıcı kodu `/eposta-dogrula` ekranında girer; başarıdan sonra oturum açılır.
- Kod için 5 yanlış deneme hakkı vardır. Sonrasında yeni kod gerekir.
- Yeniden gönderim için 60 saniye beklenir; hesap başına 15 dakikada en fazla 5
  gönderim yapılır. IP başına da ek istek sınırı uygulanır.
- Her yeni kod eski kodu ve önceki doğrulama ekranlarının tarayıcı anahtarını iptal eder.
- SMTP gönderimi başarısızsa oturum açılmaz; aynı ekrandan yeniden gönderim denenebilir.
  Tarayıcıdaki doğrulama oturumu bir saat sürer; sonra yeniden giriş yapılmalıdır.
- Mevcut normal kullanıcılar, eski oturumları olsa bile, doğrulama zorunlu olduğunda
  doğrulanana kadar uygulamaya ve API'ye erişemez. Başarıda eski oturumlar ve API
  anahtarı iptal edilir; yeni oturum oluşturulur.
- Admin ve sahip hesapları kilitlenmemeleri için bu zorunluluktan muaftır. Moderatörler
  doğrulama kapsamındadır. Sağlayıcının doğruladığı sosyal giriş adreslerinde ayrıca
  kod istenmez. Kod doğrulaması tek başına admin veya sahip rolü atamaz.

E-posta ilk kez doğrulanırken eski, doğrulanmamış erişimler temizlenir. Kodla
doğrulamada eski sosyal hesap bağlantıları kaldırılır. Doğrulanmış sosyal girişle
normal hesabın sahipliği ilk kez kanıtlanıyorsa eski parola ve diğer sosyal hesap
bağlantıları kaldırılır; kullanıcı sosyal girişle devam edebilir ve Ayarlar'dan yeni
parola belirleyebilir. Daha önce doğrulanmış hesapların bağlantıları korunur.
Parolası olmayan ve sağlayıcısı adresi doğrulamayan sosyal hesaplarda kod ekranı
bir parola da ister; böylece kullanıcı sonraki girişte e-posta ve parolasını kullanır.

Kodlar ve tarayıcı anahtarları veritabanında düz metin tutulmaz. Doğrulama durumu
hesap kaydında, gönderim ve başarı olayları denetim kaydında saklanır.

Gerçek teslimatı kontrol etmek için yeni bir normal hesapla kayıt olun; gelen
kutusu/spam klasöründen kodu alıp giriş yapın. SMTP sunucusu hatası varsa sunucu
günlüğündeki `reconclaw.mail` kaydını kontrol edin. Otomatik testler SMTP gönderimini
taklit eder; gerçek şirket sunucusuna bağlanmaz.
