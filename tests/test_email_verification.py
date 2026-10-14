import re
from contextlib import closing
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import auth, config, db_manager, mailer


@pytest.fixture
def verification_client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_manager, 'DB_PATH', str(tmp_path / 'verification.db'))
    monkeypatch.setattr(config, 'REQUIRE_EMAIL_VERIFICATION', True, raising=False)
    monkeypatch.setattr(config, 'SMTP_HOST', 'smtp.example.com')
    monkeypatch.setattr(config, 'SMTP_FROM', 'security@example.com')
    monkeypatch.setattr(config, 'ADMIN_EMAILS', set())
    monkeypatch.setattr(config, 'OWNER_EMAIL', '')
    messages = []
    monkeypatch.setattr(mailer, 'send', lambda to, subject, body: messages.append((to, subject, body)) or True)
    import main
    with TestClient(main.app) as client:
        yield client, messages


def register(client):
    return client.post('/auth/register', json={'email': 'member@example.com', 'password': 'parola123'})


def code(messages):
    return re.search(r'\b\d{6}\b', messages[-1][2]).group()


def test_registration_requires_code_before_session(verification_client):
    client, messages = verification_client
    response = register(client)
    assert response.status_code == 200
    assert response.json()['verification_required'] is True
    assert auth.SESSION_COOKIE not in client.cookies
    assert client.get('/api/me').status_code == 401
    assert messages[0][0] == 'member@example.com'
    assert '15 dakika' in messages[0][2]
    assert code(messages) not in response.text
    page = client.get('/eposta-dogrula')
    assert page.status_code == 200 and 'verificationForm' in page.text
    response = client.post('/auth/email/verify', json={'code': code(messages)})
    assert response.status_code == 200
    assert client.get('/api/me').json()['email_verified'] is True
    assert auth.user_by_email('member@example.com')['role'] == 'user'
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 400


def test_code_storage_expiry_and_single_use(verification_client):
    client, messages = verification_client
    register(client)
    with closing(db_manager.get_db_connection()) as conn, conn:
        row = conn.execute('SELECT * FROM email_verifications').fetchone()
        assert code(messages) not in str(tuple(row))
        expiry = datetime.fromisoformat(row['expires_at'])
        assert 895 <= (expiry - datetime.now()).total_seconds() <= 900
        conn.execute('UPDATE email_verifications SET expires_at = ?',
                     ((datetime.now() - timedelta(seconds=1)).isoformat(' '),))
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 400
    assert not auth.user_by_email('member@example.com')['email_verified']


def test_attempt_limit_and_resend_cooldown(verification_client):
    client, messages = verification_client
    register(client)
    assert client.post('/auth/email/resend').status_code == 429
    assert len(messages) == 1
    wrong = '000000' if code(messages) != '000000' else '111111'
    for _ in range(5):
        assert client.post('/auth/email/verify', json={'code': wrong}).status_code == 400
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 400
    with closing(db_manager.get_db_connection()) as conn, conn:
        conn.execute('UPDATE email_verifications SET sent_at = ?',
                     ((datetime.now() - timedelta(seconds=61)).isoformat(' '),))
    assert client.post('/auth/email/resend').status_code == 200
    assert len(messages) == 2
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 200


def test_login_resumes_verification_and_blocks_old_credentials(verification_client):
    client, messages = verification_client
    uid = auth.create_user('member@example.com', 'Üye', 'parola123')
    old_session = auth.create_session(uid)
    token = auth.rotate_api_token(uid)
    client.cookies.set(auth.SESSION_COOKIE, old_session)
    assert client.get('/api/me').status_code == 401
    assert client.get('/api/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401
    response = client.post('/auth/login', json={'email': 'member@example.com', 'password': 'parola123', 'remember': False})
    assert response.json()['verification_required'] is True
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 200
    assert 'Max-Age' not in client.post('/auth/login', json={
        'email': 'member@example.com', 'password': 'parola123', 'remember': False}).headers['set-cookie']
    assert auth.user_from_session(old_session) is None
    assert auth.user_from_api_token(token) is None


def test_login_can_resume_the_pending_code_without_sending_again(verification_client):
    client, messages = verification_client
    register(client)
    response = client.post('/auth/login', json={'email': 'member@example.com', 'password': 'parola123'})
    assert response.status_code == 200 and response.json()['verification_required'] is True
    assert len(messages) == 1
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 200


def test_resend_rotates_code_and_enforces_account_send_limit(verification_client, monkeypatch):
    from core import email_verification
    values = iter(range(123450, 123456))
    monkeypatch.setattr(email_verification.secrets, 'randbelow', lambda maximum: next(values))
    client, messages = verification_client
    register(client)
    first = code(messages)
    for _ in range(4):
        with closing(db_manager.get_db_connection()) as conn, conn:
            conn.execute('UPDATE email_verifications SET sent_at = ?',
                         ((datetime.now() - timedelta(seconds=61)).isoformat(' '),))
        assert client.post('/auth/email/resend').status_code == 200
    with closing(db_manager.get_db_connection()) as conn, conn:
        conn.execute('UPDATE email_verifications SET sent_at = ?',
                     ((datetime.now() - timedelta(seconds=61)).isoformat(' '),))
    assert client.post('/auth/email/resend').status_code == 429
    assert len(messages) == 5
    assert client.post('/auth/email/verify', json={'code': first}).status_code == 400
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 200


def test_existing_owner_stays_accessible(verification_client):
    client, messages = verification_client
    auth.create_user('owner@example.com', 'Sahip', 'parola123')
    auth.set_owner('owner@example.com')
    response = client.post('/auth/login', json={'email': 'owner@example.com', 'password': 'parola123'})
    assert response.status_code == 200 and not response.json().get('verification_required')
    assert client.get('/api/admin/overview').status_code == 200
    assert messages == []


def test_smtp_missing_or_failed_does_not_create_session(verification_client, monkeypatch):
    client, _ = verification_client
    monkeypatch.setattr(config, 'SMTP_HOST', '')
    assert register(client).status_code == 503
    assert auth.user_by_email('member@example.com') is None
    monkeypatch.setattr(config, 'SMTP_HOST', 'smtp.example.com')
    monkeypatch.setattr(mailer, 'send', lambda *args: False)
    assert register(client).status_code == 503
    assert auth.SESSION_COOKIE not in client.cookies
    assert client.get('/api/me').status_code == 401
    monkeypatch.setattr(mailer, 'send', lambda *args: True)
    assert client.post('/auth/email/resend').status_code == 200


def test_verification_requires_pending_cookie_and_same_origin(verification_client):
    client, messages = verification_client
    register(client)
    assert client.post('/auth/email/verify', json={'code': code(messages)},
                       headers={'Origin': 'https://evil.example'}).status_code == 403
    client.cookies.clear()
    assert client.post('/auth/email/verify', json={'code': code(messages)}).status_code == 400


def test_email_code_does_not_grant_reserved_address_admin_role(verification_client, monkeypatch):
    from core import email_verification
    uid = auth.login_with_identity('unverified-provider', 'subject', 'member@example.com', 'Üye', False)
    monkeypatch.setattr(config, 'ADMIN_EMAILS', {'member@example.com'})
    monkeypatch.setattr(config, 'OWNER_EMAIL', 'member@example.com')
    token, value = email_verification.issue(uid)
    email_verification.consume(token, value, 'newpassword123')
    assert auth.sync_admins() == 0
    assert auth.sync_owner() is False
    assert auth.get_user(uid)['role'] == 'user'


@pytest.mark.parametrize('existing_identity', [False, True])
def test_oauth_verification_revokes_unverified_account_credentials(verification_client, existing_identity):
    uid = auth.create_user('member@example.com', 'Üye', 'parola123')
    if existing_identity:
        with closing(db_manager.get_db_connection()) as conn, conn:
            conn.execute('INSERT INTO identities (user_id, provider, subject) VALUES (?, ?, ?)',
                         (uid, 'google', 'real-owner'))
    with closing(db_manager.get_db_connection()) as conn, conn:
        conn.execute('INSERT INTO identities (user_id, provider, subject) VALUES (?, ?, ?)',
                     (uid, 'other-provider', 'untrusted-subject'))
    session = auth.create_session(uid)
    api_token = auth.rotate_api_token(uid)
    reset_token = auth.create_reset_token('member@example.com')[1]
    assert auth.login_with_identity('google', 'real-owner', 'member@example.com', 'Üye', True) == uid
    assert auth.user_from_session(session) is None
    assert auth.user_from_api_token(api_token) is None
    assert auth.get_user(uid)['password_hash'] is None
    with pytest.raises(auth.AuthError):
        auth.reset_with_token(reset_token, 'hacked123')
    with closing(db_manager.get_db_connection()) as conn:
        assert [tuple(row) for row in conn.execute('SELECT provider, subject FROM identities WHERE user_id = ?', (uid,))] == [('google', 'real-owner')]


def test_code_verification_removes_untrusted_social_identities(verification_client):
    from core import email_verification
    uid = auth.create_user('member@example.com', 'Üye', 'parola123')
    with closing(db_manager.get_db_connection()) as conn, conn:
        conn.execute('INSERT INTO identities (user_id, provider, subject) VALUES (?, ?, ?)',
                     (uid, 'unverified-provider', 'attacker'))
    token, value = email_verification.issue(uid)
    email_verification.consume(token, value)
    with closing(db_manager.get_db_connection()) as conn:
        assert conn.execute('SELECT COUNT(*) FROM identities WHERE user_id = ?', (uid,)).fetchone()[0] == 0
    assert auth.authenticate('member@example.com', 'parola123') == uid


def test_passwordless_social_user_sets_password_during_code_verification(verification_client):
    from core import email_verification
    client, _ = verification_client
    uid = auth.login_with_identity('unverified-provider', 'subject', 'member@example.com', 'Üye', False)
    token, value = email_verification.issue(uid)
    client.cookies.set(email_verification.COOKIE, token)
    assert 'id="verificationPassword"' in client.get('/eposta-dogrula').text
    assert client.post('/auth/email/verify', json={'code': value}).status_code == 400
    assert not auth.get_user(uid)['email_verified']
    assert client.post('/auth/email/verify', json={'code': value, 'password': 'newpassword123'}).status_code == 200
    client.post('/auth/logout')
    response = client.post('/auth/login', json={'email': 'member@example.com', 'password': 'newpassword123'})
    assert response.status_code == 200 and not response.json().get('verification_required')
