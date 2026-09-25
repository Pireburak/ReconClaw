import asyncio
import re
import ssl

from core.plugins import Plugin

TLS_PORTS = {443, 8443}

# başlık -> (şiddet, eksikse gösterilecek açıklama)
SECURITY_HEADERS = {
    "content-security-policy": ("medium", "XSS ve içerik enjeksiyonuna karşı CSP tanımlayın."),
    "x-frame-options": ("low", "Clickjacking'e karşı X-Frame-Options: DENY veya CSP frame-ancestors kullanın."),
    "x-content-type-options": ("low", "MIME sniffing'i engellemek için X-Content-Type-Options: nosniff ekleyin."),
    "referrer-policy": ("info", "Referrer-Policy ile dışarıya sızan URL bilgisini sınırlayın."),
}


class HttpHeadersPlugin(Plugin):
    name = "http_headers"
    description = "HTTP güvenlik başlıklarını ve sürüm ifşasını kontrol eder."
    ports = {80, 443, 8000, 8008, 8080, 8443, 8888}

    async def fetch_headers(self, target, ip, port):
        use_tls = port in TLS_PORTS
        ctx = None
        if use_tls:
            # Sertifika geçerliliği tls_cert eklentisinin işi; burada sadece başlıkları okuyoruz
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port, ssl=ctx, server_hostname=target if use_tls else None),
            timeout=self.timeout,
        )
        try:
            writer.write(f"GET / HTTP/1.0\r\nHost: {target}\r\nUser-Agent: ReconClaw\r\n\r\n".encode())
            await writer.drain()
            raw = await asyncio.wait_for(reader.read(16384), timeout=self.timeout)
        finally:
            writer.close()
        head = raw.decode("iso-8859-1").split("\r\n\r\n", 1)[0]
        lines = head.split("\r\n")
        if not lines or not lines[0].startswith("HTTP/"):
            return None, use_tls
        headers = {}
        for line in lines[1:]:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
        return headers, use_tls

    async def check(self, target, ip, port):
        headers, use_tls = await self.fetch_headers(target, ip, port)
        if headers is None:
            return []

        findings = []
        for header, (severity, advice) in SECURITY_HEADERS.items():
            if header not in headers:
                findings.append(self.finding(port, severity, f"Eksik başlık: {header}", advice))

        if use_tls and "strict-transport-security" not in headers:
            findings.append(self.finding(port, "medium", "Eksik başlık: strict-transport-security",
                                         "HTTPS'i zorunlu kılmak için HSTS başlığı ekleyin."))

        for header in ("server", "x-powered-by"):
            value = headers.get(header, "")
            if re.search(r"\d", value):
                findings.append(self.finding(port, "low", f"Sürüm ifşası: {header}: {value}",
                                             "Sunucu yapılandırmasında sürüm bilgisini gizleyin."))
        return findings
