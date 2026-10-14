"""15 dakikalık e-posta kodları. Kod ve tarayıcı anahtarı yalnızca özet olarak saklanır."""
import secrets
from contextlib import closing
from datetime import timedelta

from core import auth, config
from core.db_manager import get_db_connection

COOKIE = 'rc_email_verification'
MINUTES = 15
MAX_ATTEMPTS = 5
COOLDOWN = 60
PENDING_SECONDS = 3600


class VerificationError(auth.AuthError):
    pass


class VerificationLimit(VerificationError):
    pass


def required(user):
    return bool(user is not None and config.REQUIRE_EMAIL_VERIFICATION and
                not user['email_verified'] and user['role'] not in ('admin', 'owner'))


def pending(token):
    if not token:
        return None
    with closing(get_db_connection()) as conn:
        return conn.execute(
            'SELECT v.*, u.email, u.name, u.password_hash IS NOT NULL AS has_password FROM email_verifications v JOIN users u ON u.id = v.user_id '
            'WHERE challenge_hash = ? AND v.created_at > ? AND u.disabled = 0 AND u.email_verified = 0',
            (auth._sha256(token), (auth._now() - timedelta(seconds=PENDING_SECONDS)).isoformat(' ')),
        ).fetchone()


def issue(user_id, remember=True):
    now = auth._now()
    with closing(get_db_connection()) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user is None or user['disabled'] or user['email_verified']:
            raise VerificationError('Hesap doğrulanamıyor. Yeniden giriş yapın.')
        old = conn.execute('SELECT * FROM email_verifications WHERE user_id = ?', (user_id,)).fetchone()
        sends, window = 0, now.isoformat(' ')
        if old:
            if old['sent_at'] > (now - timedelta(seconds=COOLDOWN)).isoformat(' '):
                raise VerificationLimit('Yeni kod için 60 saniye bekleyin.')
            if old['send_window'] > (now - timedelta(minutes=MINUTES)).isoformat(' '):
                sends, window = old['sends'], old['send_window']
            if sends >= 5:
                raise VerificationLimit('Çok fazla kod istendi. 15 dakika sonra tekrar deneyin.')
        # Each send rotates the browser challenge too; previous tabs cannot consume the new code.
        token = secrets.token_urlsafe(32)
        code = f'{secrets.randbelow(1000000):06d}'
        conn.execute(
            'INSERT OR REPLACE INTO email_verifications '
            '(user_id, challenge_hash, code_hash, created_at, expires_at, sent_at, attempts, sends, send_window, remember) '
            'VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)',
            (user_id, auth._sha256(token), auth.hash_password(code), now.isoformat(' '),
             (now + timedelta(minutes=MINUTES)).isoformat(' '), now.isoformat(' '), sends + 1, window, int(remember)),
        )
    return token, code


def delivery_failed(token):
    with closing(get_db_connection()) as conn, conn:
        conn.execute("UPDATE email_verifications SET sent_at = '' WHERE challenge_hash = ?", (auth._sha256(token),))


def consume(token, code, password=None):
    error = 'Kod geçersiz veya süresi dolmuş. Yeni kod isteyin.'
    result = None
    with closing(get_db_connection()) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute(
            'SELECT v.*, u.disabled, u.password_hash FROM email_verifications v JOIN users u ON u.id = v.user_id '
            'WHERE challenge_hash = ?', (auth._sha256(token or ''),)).fetchone()
        if row and not row['disabled'] and row['expires_at'] > auth._now().isoformat(' ') and row['attempts'] < MAX_ATTEMPTS:
            if auth.verify_password(code, row['code_hash']):
                if not row['password_hash']:
                    if not password:
                        raise VerificationError('Sonraki girişleriniz için bir parola belirleyin.')
                    auth.validate_password(password)
                    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                                 (auth.hash_password(password), row['user_id']))
                conn.execute("UPDATE users SET email_verified = 1, email_verified_by = 'code', api_token = NULL WHERE id = ?", (row['user_id'],))
                conn.execute('DELETE FROM sessions WHERE user_id = ?', (row['user_id'],))
                conn.execute('DELETE FROM identities WHERE user_id = ?', (row['user_id'],))
                conn.execute('DELETE FROM password_resets WHERE user_id = ?', (row['user_id'],))
                conn.execute('DELETE FROM email_verifications WHERE user_id = ?', (row['user_id'],))
                result = row['user_id'], bool(row['remember'])
            else:
                conn.execute('UPDATE email_verifications SET attempts = attempts + 1 WHERE user_id = ?', (row['user_id'],))
    # Raise after committing: incorrect guesses must consume their persisted attempt.
    if result is None:
        raise VerificationError(error)
    return result
