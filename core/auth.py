"""
Kullanıcı hesapları ve oturumlar.

  * Parolalar tuzlu scrypt ile saklanır (düz metin asla veritabanına yazılmaz).
  * Oturum, tarayıcıdaki HttpOnly çerezde tutulan rastgele bir anahtardır; veritabanında
    yalnızca SHA-256 özeti saklanır. Çıkış yapılınca kayıt silinir.
  * API anahtarı (Authorization: Bearer rc_...) ile arayüz olmadan da API kullanılabilir.
"""

import base64
import hashlib
import hmac
import re
import secrets
from contextlib import closing
from datetime import datetime, timedelta

from core import config
from core.db_manager import get_db_connection

SESSION_COOKIE = "rc_session"
API_TOKEN_PREFIX = "rc_"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8

_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


class AuthError(Exception):
    """Kullanıcıya gösterilebilecek kimlik doğrulama hatası."""


def _now():
    return datetime.now().replace(microsecond=0)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ---------------------------------------------------------------- parolalar
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, dklen=32, **_SCRYPT)
    b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _, n, r, p, salt, digest = stored.split("$")
        expected = base64.b64decode(digest)
        actual = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt),
                                n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def validate_password(password: str):
    if len(password) < MIN_PASSWORD:
        raise AuthError(f"Parola en az {MIN_PASSWORD} karakter olmalı.")
    if password.isdigit() or password.isalpha():
        raise AuthError("Parola hem harf hem rakam/sembol içermeli.")


# ---------------------------------------------------------------- kullanıcılar
def public_user(row) -> dict:
    """Kullanıcı kaydının arayüze gönderilebilecek hali (parola özeti vb. olmadan)."""
    if row is None:
        return None
    with closing(get_db_connection()) as conn:
        providers = [r["provider"] for r in conn.execute(
            "SELECT provider FROM identities WHERE user_id = ? ORDER BY provider", (row["id"],))]
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "avatar_url": row["avatar_url"],
        "has_password": bool(row["password_hash"]),
        "has_api_token": bool(row["api_token"]),
        "providers": providers,
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


def get_user(user_id):
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def _claim_orphan_scans(conn, user_id):
    # Kimlik doğrulama gelmeden önce yapılmış taramalar ilk kullanıcıya devredilir
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1:
        conn.execute("UPDATE scans SET user_id = ? WHERE user_id IS NULL", (user_id,))


def create_user(email: str, name: str, password: str | None = None, avatar_url=None, check_signup=True):
    email = email.strip().lower()
    name = (name or "").strip() or email.split("@")[0]
    if check_signup and not config.ALLOW_SIGNUP:
        raise AuthError("Yeni kayıtlar yönetici tarafından kapatıldı.")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise AuthError("Geçerli bir e-posta adresi girin.")
    if password is not None:
        validate_password(password)
    with closing(get_db_connection()) as conn, conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise AuthError("Bu e-posta ile kayıtlı bir hesap zaten var.")
        cur = conn.execute(
            "INSERT INTO users (email, name, password_hash, avatar_url, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, name[:80], hash_password(password) if password else None, avatar_url, _now().isoformat(" ")),
        )
        _claim_orphan_scans(conn, cur.lastrowid)
        return cur.lastrowid


def authenticate(email: str, password: str):
    with closing(get_db_connection()) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row is None:
        # Kullanıcı yokken de aynı sürede yanıt vermek için sahte doğrulama yap
        verify_password(password, hash_password("zamanlama-esitleme"))
        raise AuthError("E-posta veya parola hatalı.")
    if not row["password_hash"]:
        raise AuthError("Bu hesap sosyal giriş ile açılmış. Lütfen ilgili butonla giriş yapın.")
    if not verify_password(password, row["password_hash"]):
        raise AuthError("E-posta veya parola hatalı.")
    return row["id"]


def update_profile(user_id, name: str):
    name = name.strip()
    if not name:
        raise AuthError("Ad boş olamaz.")
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name[:80], user_id))


def change_password(user_id, current: str | None, new: str):
    row = get_user(user_id)
    if row["password_hash"] and not verify_password(current or "", row["password_hash"]):
        raise AuthError("Mevcut parola hatalı.")
    validate_password(new)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), user_id))


def delete_user(user_id):
    with closing(get_db_connection()) as conn, conn:
        conn.execute("DELETE FROM scans WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def login_with_identity(provider: str, subject: str, email: str | None, name: str,
                        email_verified: bool, avatar_url=None) -> int:
    """Sosyal girişte kullanıcıyı bulur, gerekirse bağlar veya oluşturur; kullanıcı id'sini döndürür."""
    with closing(get_db_connection()) as conn:
        row = conn.execute(
            "SELECT user_id FROM identities WHERE provider = ? AND subject = ?", (provider, subject)
        ).fetchone()
        if row:
            return row["user_id"]
        existing = conn.execute("SELECT id FROM users WHERE email = ?", ((email or "").lower(),)).fetchone()

    if existing:
        # Aynı e-postalı mevcut hesaba yalnızca sağlayıcı e-postayı doğruladıysa bağlanır;
        # aksi halde başkası o e-postayı yazarak hesabı ele geçirebilirdi.
        if not email_verified:
            raise AuthError("Bu e-posta başka bir hesapta kayıtlı ve sağlayıcı e-postayı doğrulamadı.")
        user_id = existing["id"]
    else:
        if not email:
            raise AuthError("Sağlayıcı e-posta adresinizi paylaşmadı; e-posta izni vererek tekrar deneyin.")
        user_id = create_user(email, name, avatar_url=avatar_url)

    with closing(get_db_connection()) as conn, conn:
        conn.execute("INSERT INTO identities (user_id, provider, subject) VALUES (?, ?, ?)",
                     (user_id, provider, subject))
        if avatar_url:
            conn.execute("UPDATE users SET avatar_url = COALESCE(avatar_url, ?) WHERE id = ?", (avatar_url, user_id))
    return user_id


# ---------------------------------------------------------------- oturumlar
def create_session(user_id, user_agent="", days=None) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()
    expires = now + timedelta(days=days or config.SESSION_DAYS)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(" "),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at, user_agent) VALUES (?, ?, ?, ?, ?)",
            (_sha256(token), user_id, now.isoformat(" "), expires.isoformat(" "), (user_agent or "")[:200]),
        )
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now.isoformat(" "), user_id))
    return token


def user_from_session(token: str | None):
    if not token:
        return None
    with closing(get_db_connection()) as conn:
        return conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (_sha256(token), _now().isoformat(" ")),
        ).fetchone()


def user_from_api_token(token: str | None):
    if not token or not token.startswith(API_TOKEN_PREFIX):
        return None
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT * FROM users WHERE api_token = ?", (_sha256(token),)).fetchone()


def delete_session(token: str | None):
    if token:
        with closing(get_db_connection()) as conn, conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_sha256(token),))


def delete_other_sessions(user_id, keep_token: str | None):
    with closing(get_db_connection()) as conn, conn:
        cur = conn.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
                           (user_id, _sha256(keep_token or "")))
        return cur.rowcount


def count_sessions(user_id):
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ? AND expires_at > ?",
                            (user_id, _now().isoformat(" "))).fetchone()[0]


def rotate_api_token(user_id, revoke=False) -> str | None:
    """Yeni bir API anahtarı üretir (yalnızca bir kez gösterilir) veya mevcut anahtarı iptal eder."""
    token = None if revoke else API_TOKEN_PREFIX + secrets.token_urlsafe(30)
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE users SET api_token = ? WHERE id = ?", (token and _sha256(token), user_id))
    return token
