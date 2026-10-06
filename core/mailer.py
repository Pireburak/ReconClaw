"""
E-posta gönderimi (SMTP). Şimdilik yalnızca şifre sıfırlama bağlantısı için kullanılır.

SMTP_HOST boşsa e-posta özelliği kapalıdır ve "Şifremi unuttum" bağlantısı gösterilmez.
Gmail / Google Workspace için uygulama şifresi, Yandex / Zoho / Brevo gibi servisler için SMTP bilgileri kullanılır.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from core import config

log = logging.getLogger("reconclaw.mail")


def enabled() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_FROM)


def send(to: str, subject: str, text: str) -> bool:
    """Düz metin e-posta gönderir (eşzamanlı; çağıran tarafta run_in_threadpool ile kullanın)."""
    if not enabled():
        return False
    msg = EmailMessage()
    msg["From"] = formataddr((config.COMPANY_NAME, config.SMTP_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=config.SMTP_FROM.split("@")[-1])
    msg.set_content(text)
    context = ssl.create_default_context()
    try:
        if config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20, context=context)
        else:
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
            if config.SMTP_TLS:
                server.starttls(context=context)
        with server:
            if config.SMTP_USER:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        log.warning("E-posta gönderilemedi (%s): %s", to, exc)
        return False
