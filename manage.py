"""
ReconClaw yönetim komutları.

    python manage.py make-admin ornek@mail.com     # hesabı yönetici yap (sınırsız erişim + Yönetim paneli)
    python manage.py remove-admin ornek@mail.com   # yönetici rolünü kaldır
    python manage.py list-admins                   # yöneticileri listele

Hesabın önceden açılmış olması gerekir (siteye bir kez kayıt olun veya sosyal girişle girin).
Alternatif olarak .env dosyasına ADMIN_EMAILS=ornek@mail.com yazabilirsiniz.
"""

import sys
from contextlib import closing

from core import auth
from core.db_manager import get_db_connection, init_db


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    init_db()
    if not argv or argv[0] not in ("make-admin", "remove-admin", "list-admins"):
        print(__doc__)
        return 2
    if argv[0] == "list-admins":
        with closing(get_db_connection()) as conn:
            rows = conn.execute("SELECT email, name FROM users WHERE role = 'admin' ORDER BY id").fetchall()
        for row in rows:
            print(f"  {row['email']}  ({row['name']})")
        print(f"{len(rows)} yönetici")
        return 0
    if len(argv) < 2:
        print("E-posta adresi gerekli.")
        return 2
    role = "admin" if argv[0] == "make-admin" else "user"
    if not auth.set_role(argv[1], role):
        print(f"Hesap bulunamadı: {argv[1]} (önce siteye kayıt olun)")
        return 1
    print(f"{argv[1]} → {'YÖNETİCİ' if role == 'admin' else 'normal kullanıcı'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
