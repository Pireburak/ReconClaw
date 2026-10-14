# Google ve GitHub ile giriş

ReconClaw iki sağlayıcıyı destekler. Butonlar, ilgili Client ID ve Client Secret
sunucudaki `.env` dosyasına eklendiğinde etkinleşir. Aşağıdaki adresler canlı
`https://reconclaw.com.tr` kurulumu içindir. Farklı alan adı kullanıyorsanız hem
`PUBLIC_URL` hem sağlayıcıdaki callback adresini aynı alan adına göre değiştirin.

## Google

1. [Google Cloud Console](https://console.cloud.google.com/) üzerinden bir proje
   seçin veya ReconClaw adına bir proje oluşturun.
2. Google Auth Platform kurulumunda uygulama adını ReconClaw yapın; destek ve
   iletişim e-postalarını kendi adreslerinizle doldurun. Genel kullanıma açık site
   için kitleyi External seçin.
3. Branding alanlarında site adresi `https://reconclaw.com.tr`, gizlilik politikası
   `https://reconclaw.com.tr/yasal/gizlilik`, kullanım şartları
   `https://reconclaw.com.tr/yasal/kullanim` ve yetkili alan adı
   `reconclaw.com.tr` kullanılabilir. Panel isterse alan adı sahipliğini doğrulayın.
4. [Clients](https://console.cloud.google.com/auth/clients) → Create client →
   **Web application** seçin.
5. Authorized redirect URIs alanına tam olarak şunu yazın:
   `https://reconclaw.com.tr/auth/google/callback`
6. İstemciyi oluşturup Client ID ve Client Secret değerlerini sunucudaki `.env`
   dosyasına yazın. SMTP için oluşturduğunuz Google uygulama şifresini burada kullanmayın.
7. Testing durumundaysanız kendi hesabınızı Audience → Test users bölümüne ekleyin.
   Herkese açarken Audience bölümündeki yayın durumunu ve Google'ın istediği
   doğrulama adımlarını tamamlayın.

Bu uygulama sunucu üzerinden yönlendirme yapar; JavaScript origins alanını
doldurmak gerekli değildir. Eklemeyi tercih ederseniz `https://reconclaw.com.tr`
kullanın. Kullanılan kapsamlar yalnızca `openid email profile` şeklindedir.

## GitHub

1. [New OAuth App](https://github.com/settings/applications/new) sayfasını açın.
2. Application name: **ReconClaw**
3. Homepage URL: `https://reconclaw.com.tr`
4. Authorization callback URL:
   `https://reconclaw.com.tr/auth/github/callback`
5. Register application ile oluşturun. Client ID'yi alın, Generate a new client
   secret ile secret oluşturun; ikisini sunucudaki `.env` dosyasına yazın.

GitHub App yerine **OAuth App** oluşturun; mevcut entegrasyon bu tür içindir.
Device Flow gerekmez. Uygulama `read:user user:email` ister; depo erişimi istemez.

## Sunucudaki ayarlar

```bash
cd ~/ReconClaw
nano .env
```

Var olan satırları güncelleyin veya eksikse ekleyin. Örnek değerler yerine
panellerden aldığınız gerçek değerleri kullanın; `.env` dosyasını Git'e eklemeyin.

```dotenv
PUBLIC_URL=https://reconclaw.com.tr
GOOGLE_CLIENT_ID=GOOGLE_PANELINDEKI_CLIENT_ID
GOOGLE_CLIENT_SECRET=GOOGLE_PANELINDEKI_CLIENT_SECRET
GITHUB_CLIENT_ID=GITHUB_PANELINDEKI_CLIENT_ID
GITHUB_CLIENT_SECRET=GITHUB_PANELINDEKI_CLIENT_SECRET
```

Kaydet: Ctrl+O, Enter, Ctrl+X. Ortam değişkenlerini konteynere yükleyin:

```bash
docker compose up -d --build --force-recreate reconclaw
```

Secret'ları göstermeden etkinliği ve callback adreslerini kontrol edin:

```bash
docker compose exec reconclaw python -c "from core import oauth; print([p for p in oauth.provider_status() if p['name'] in ('google','github')]); print(oauth.redirect_uri('', 'google')); print(oauth.redirect_uri('', 'github'))"
```

İki sağlayıcıda da `enabled: True` görülmeli ve iki callback adresi yukarıdakilerle
eşleşmeli. Bu kontrol yalnızca yapılandırmayı doğrular; gerçek ID/Secret'in kabulünü
kanıtlamaz. Sonrasında `/login` ekranında her iki butonla ayrı ayrı giriş yapın.

Google `redirect_uri_mismatch` hatasında PUBLIC_URL ve Google'a girilen callback
adresinin HTTPS, alan adı ve yol dahil birebir eşleştiğini kontrol edin. Buton pasifse
ilgili sağlayıcının iki ayarı da konteynere yüklenmemiştir.

Doğrulanmış sağlayıcı e-postasında ayrıca e-posta kodu istenmez. Mevcut doğrulanmamış
normal hesabın ilk doğrulanmış sosyal girişinde eski güvenilmeyen erişimler iptal
edilebilir; ayrıntılar [e-posta doğrulama rehberinde](email-verification.md).

Resmi kaynaklar: [Google web sunucusu OAuth kurulumu](https://developers.google.com/identity/protocols/oauth2/web-server),
[Google uygulama markası doğrulaması](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification),
[GitHub OAuth uygulaması oluşturma](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).
