"""
ReconClaw yönetim komutları (sunucunun terminalinden çalıştırılır).

    python manage.py make-owner ornek@mail.com     # hesabı sistemin tek sahibi yap (silinemez)
    python manage.py make-admin ornek@mail.com     # hesabı yönetici yap
    python manage.py remove-admin ornek@mail.com   # yönetici rolünü kaldır
    python manage.py list-admins                   # sahip ve yöneticileri listele
    python manage.py passwd ornek@mail.com         # parolayı sıfırla (oturumlar kapanır)

Hesabın önceden açılmış olması gerekir (siteye bir kez kayıt olun veya sosyal girişle girin).
"""

import getpass
import sys
from contextlib import closing

from core import auth
from core.db_manager import get_db_connection, init_db

COMMANDS = ("make-owner", "make-admin", "remove-admin", "list-admins", "passwd")


def _role_of(email: str):
    user = auth.user_by_email(email)
    return None if user is None else user["role"]


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    init_db()
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "list-admins":
        with closing(get_db_connection()) as conn:
            rows = conn.execute("SELECT email, name, role FROM users WHERE role IN ('owner', 'admin') "
                                "ORDER BY role = 'owner' DESC, id").fetchall()
        for row in rows:
            print(f"  {row['email']:<32} {'SAHİP' if row['role'] == 'owner' else 'yönetici':<9} ({row['name']})")
        print(f"{len(rows)} hesap")
        return 0
    if len(argv) < 2:
        print("E-posta adresi gerekli.")
        return 2
    email = argv[1]
    role = _role_of(email)
    if role is None:
        print(f"Hesap bulunamadı: {email} (önce siteye kayıt olun)")
        return 1

    if cmd == "make-owner":
        auth.set_owner(email)
        print(f"{email} → SAHİP (önceki sahip varsa yöneticiye indi)")
    elif cmd == "make-admin":
        if role == "owner":
            print(f"{email} zaten sahip; değişiklik yapılmadı.")
            return 0
        auth.set_role(email, "admin")
        print(f"{email} → YÖNETİCİ")
    elif cmd == "remove-admin":
        if role == "owner":
            print("Sahibin yetkisi alınamaz. Önce sahipliği başka hesaba devredin: make-owner <e-posta>")
            return 1
        auth.set_role(email, "user")
        print(f"{email} → normal kullanıcı")
    elif cmd == "passwd":
        password = getpass.getpass("Yeni parola: ")
        try:
            auth.reset_password(email, password)
        except auth.AuthError as exc:
            print(exc)
            return 1
        print(f"{email} parolası güncellendi; açık oturumları kapatıldı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
