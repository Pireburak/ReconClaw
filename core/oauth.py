"""
Sosyal giriş (OAuth 2.0 / OpenID Connect): Google, GitHub, Microsoft ve Apple.

Bir sağlayıcı, ilgili ortam değişkenleri (.env) doldurulduğunda giriş ekranında
etkinleşir. Uygulama kayıtlarında yönlendirme (callback) adresi olarak şunu girin:

    {PUBLIC_URL}/auth/{sağlayıcı}/callback      ör. https://reconclaw.site.com/auth/google/callback

Akış: /auth/{p}/login -> sağlayıcının onay ekranı -> /auth/{p}/callback -> kod, sunucudan
sunucuya erişim anahtarıyla değiştirilir -> profil/e-posta alınır -> oturum açılır.
`state` parametresi veritabanında tek kullanımlık saklanır (CSRF koruması);
Google ve Microsoft akışlarında ayrıca PKCE (S256) kullanılır.
"""

import base64
import hashlib
import json
import secrets
import time
from contextlib import closing
from urllib.parse import urlencode

import httpx

from core import config
from core.db_manager import get_db_connection

STATE_TTL = 600  # saniye


class OAuthError(Exception):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _jwt_claims(token: str) -> dict:
    """JWT gövdesini okur. id_token doğrudan sağlayıcının token uç noktasından TLS ile
    alındığı için imza doğrulaması yerine TLS sunucu doğrulaması yeterlidir (OIDC Core 3.1.3.7)."""
    try:
        payload = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError) as exc:
        raise OAuthError("Geçersiz kimlik belirteci.") from exc


class Provider:
    name = ""
    label = ""
    authorize_url = ""
    token_url = ""
    scope = ""
    pkce = True
    extra_params: dict = {}

    @property
    def client_id(self):
        return config.env(f"{self.name.upper()}_CLIENT_ID")

    @property
    def client_secret(self):
        return config.env(f"{self.name.upper()}_CLIENT_SECRET")

    @property
    def enabled(self):
        return bool(self.client_id and self.client_secret)

    def authorize(self, redirect_uri, state, verifier):
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
            **self.extra_params,
        }
        if self.pkce:
            params["code_challenge"] = _b64url(hashlib.sha256(verifier.encode()).digest())
            params["code_challenge_method"] = "S256"
        return f"{self.authorize_url}?{urlencode(params)}"

    async def exchange(self, client, code, redirect_uri, verifier) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.pkce:
            data["code_verifier"] = verifier
        res = await client.post(self.token_url, data=data, headers={"Accept": "application/json"})
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        if res.status_code >= 400 or "error" in body or not body:
            raise OAuthError(f"{self.label} erişim anahtarı alınamadı: {body.get('error_description') or body.get('error') or res.status_code}")
        return body

    async def profile(self, client, tokens, form) -> dict:
        """{'subject', 'email', 'email_verified', 'name', 'avatar_url'} döndürür."""
        raise NotImplementedError


class OIDCProvider(Provider):
    userinfo_url = ""

    async def profile(self, client, tokens, form):
        res = await client.get(self.userinfo_url, headers={"Authorization": f"Bearer {tokens['access_token']}"})
        res.raise_for_status()
        info = res.json()
        return {
            "subject": str(info["sub"]),
            "email": info.get("email"),
            "email_verified": info.get("email_verified") is True,
            "name": info.get("name") or "",
            "avatar_url": info.get("picture"),
        }


class GoogleProvider(OIDCProvider):
    name, label = "google", "Google"
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    scope = "openid email profile"
    extra_params = {"prompt": "select_account"}


class MicrosoftProvider(OIDCProvider):
    name, label = "microsoft", "Microsoft"
    authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    userinfo_url = "https://graph.microsoft.com/oidc/userinfo"
    scope = "openid email profile"

    async def profile(self, client, tokens, form):
        info = await super().profile(client, tokens, form)
        # Microsoft hesaplarında e-posta alanı kullanıcı tarafından değiştirilebilir; güvenmiyoruz
        info["email_verified"] = False
        info["avatar_url"] = None
        return info


class GitHubProvider(Provider):
    name, label = "github", "GitHub"
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    scope = "read:user user:email"
    pkce = False

    async def profile(self, client, tokens, form):
        headers = {"Authorization": f"Bearer {tokens['access_token']}", "Accept": "application/vnd.github+json"}
        user = (await client.get("https://api.github.com/user", headers=headers)).json()
        emails = (await client.get("https://api.github.com/user/emails", headers=headers)).json()
        primary = next((e for e in emails if isinstance(e, dict) and e.get("primary")), None) if isinstance(emails, list) else None
        return {
            "subject": str(user["id"]),
            "email": primary["email"] if primary else user.get("email"),
            "email_verified": bool(primary and primary.get("verified")),
            "name": user.get("name") or user.get("login") or "",
            "avatar_url": user.get("avatar_url"),
        }


class AppleProvider(Provider):
    """Sign in with Apple. İstemci sırrı yerine, Apple'dan indirilen .p8 anahtarıyla
    imzalanan kısa ömürlü bir ES256 JWT kullanılır (PyJWT + cryptography gerekir)."""

    name, label = "apple", "Apple"
    authorize_url = "https://appleid.apple.com/auth/authorize"
    token_url = "https://appleid.apple.com/auth/token"
    scope = "name email"
    pkce = False
    # İsim/e-posta istendiğinde Apple sonucu POST form olarak geri gönderir
    extra_params = {"response_mode": "form_post"}

    @property
    def private_key(self):
        key = config.env("APPLE_PRIVATE_KEY").replace("\\n", "\n")
        path = config.env("APPLE_PRIVATE_KEY_PATH")
        if not key and path:
            try:
                with open(path, encoding="utf-8") as fh:
                    key = fh.read()
            except OSError:
                return ""
        return key

    @property
    def enabled(self):
        return bool(self.client_id and config.env("APPLE_TEAM_ID") and config.env("APPLE_KEY_ID") and self.private_key)

    @property
    def client_secret(self):
        import jwt  # yalnızca Apple etkinse gerekli

        now = int(time.time())
        return jwt.encode(
            {"iss": config.env("APPLE_TEAM_ID"), "iat": now, "exp": now + 300,
             "aud": "https://appleid.apple.com", "sub": self.client_id},
            self.private_key, algorithm="ES256", headers={"kid": config.env("APPLE_KEY_ID")},
        )

    async def profile(self, client, tokens, form):
        claims = _jwt_claims(tokens.get("id_token", ""))
        if claims.get("iss") != "https://appleid.apple.com" or claims.get("aud") != self.client_id:
            raise OAuthError("Apple kimlik belirteci bu uygulama için değil.")
        name = ""
        try:  # İsim yalnızca ilk girişte, 'user' form alanında gelir
            n = json.loads(form.get("user", "{}")).get("name", {})
            name = f"{n.get('firstName', '')} {n.get('lastName', '')}".strip()
        except (ValueError, AttributeError):
            pass
        return {
            "subject": str(claims["sub"]),
            "email": claims.get("email"),
            "email_verified": str(claims.get("email_verified")).lower() == "true",
            "name": name,
            "avatar_url": None,
        }


PROVIDERS = {p.name: p for p in (GoogleProvider(), GitHubProvider(), MicrosoftProvider(), AppleProvider())}


def provider_status():
    return [{"name": p.name, "label": p.label, "enabled": p.enabled} for p in PROVIDERS.values()]


def redirect_uri(base_url: str, provider: str) -> str:
    return f"{config.PUBLIC_URL or base_url.rstrip('/')}/auth/{provider}/callback"


def new_state(provider: str) -> tuple[str, str]:
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("DELETE FROM oauth_states WHERE created_at < ?", (time.time() - STATE_TTL,))
        conn.execute("INSERT INTO oauth_states (state, provider, verifier, created_at) VALUES (?, ?, ?, ?)",
                     (state, provider, verifier, time.time()))
    return state, verifier


def consume_state(provider: str, state: str) -> str:
    """state'i doğrular ve siler (tek kullanımlık); PKCE doğrulayıcısını döndürür."""
    with closing(get_db_connection()) as conn, conn:
        row = conn.execute("SELECT * FROM oauth_states WHERE state = ?", (state or "",)).fetchone()
        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state or "",))
    if row is None or row["provider"] != provider or row["created_at"] < time.time() - STATE_TTL:
        raise OAuthError("Giriş isteğinin süresi doldu veya geçersiz. Lütfen tekrar deneyin.")
    return row["verifier"]


async def complete_login(provider: Provider, code: str, redirect: str, verifier: str, form: dict) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        tokens = await provider.exchange(client, code, redirect, verifier)
        try:
            return await provider.profile(client, tokens, form)
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            raise OAuthError(f"{provider.label} profil bilgisi alınamadı.") from exc
