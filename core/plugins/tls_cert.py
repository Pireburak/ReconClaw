import asyncio
import ipaddress
import ssl
from datetime import datetime, timezone

from core.plugins import Plugin

WEAK_PROTOCOLS = {"SSLv3", "TLSv1", "TLSv1.1"}


def _is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


class TlsCertPlugin(Plugin):
    name = "tls_cert"
    description = "TLS sertifikasının geçerliliğini, bitiş tarihini ve protokol sürümünü kontrol eder."
    ports = {443, 465, 636, 993, 995, 8443}

    async def handshake(self, ip, port, ctx, server_hostname):
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port, ssl=ctx, server_hostname=server_hostname),
            timeout=self.timeout,
        )
        try:
            tls = writer.get_extra_info("ssl_object")
            return tls.getpeercert(), tls.version()
        finally:
            writer.close()

    async def check(self, target, ip, port):
        findings = []
        ctx = ssl.create_default_context()
        # IP ile taranan hedeflerde isim doğrulaması anlamsız; zincir yine doğrulanır
        ctx.check_hostname = not _is_ip(target)
        try:
            cert, version = await self.handshake(ip, port, ctx, target)
        except ssl.SSLCertVerificationError as exc:
            findings.append(self.finding(port, "high", "Sertifika doğrulanamadı",
                                         f"{exc.verify_message}. Güvenilir bir CA'dan geçerli sertifika kullanın."))
            # Protokol sürümünü yine de öğrenmek için doğrulamasız bağlan
            loose = ssl.create_default_context()
            loose.check_hostname = False
            loose.verify_mode = ssl.CERT_NONE
            cert, version = await self.handshake(ip, port, loose, target)

        if version in WEAK_PROTOCOLS:
            findings.append(self.finding(port, "high", f"Zayıf protokol: {version}",
                                         "TLS 1.0/1.1 desteğini kapatın, en az TLS 1.2 kullanın."))

        if cert and "notAfter" in cert:
            expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc)
            days = (expires - datetime.now(timezone.utc)).days
            if 0 <= days < 30:
                findings.append(self.finding(port, "medium", f"Sertifikanın süresi {days} gün içinde doluyor",
                                             f"Bitiş: {expires:%Y-%m-%d}. Sertifikayı yenileyin."))
            elif days >= 30:
                findings.append(self.finding(port, "info", f"Sertifika geçerli ({days} gün kaldı)",
                                             f"Bitiş: {expires:%Y-%m-%d}, protokol: {version}"))
        return findings
