"""
ReconClaw tarama motoru.

İki ana parçadan oluşur:
  * AsyncScanner  -> DNS çözümleme + asenkron TCP connect taraması + banner yakalama
  * RiskAnalyzer  -> Açık portlardan risk skoru, CVE uyarıları ve öneriler üretir
"""

import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse

from core.plugins import SEVERITY_WEIGHTS

# Varsayılan olarak taranan, sık kullanılan ve güvenlik açısından önemli portlar
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
    1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017,
]

# port -> (servis adı, risk ağırlığı)
SERVICE_MAP = {
    21: ("FTP", 15),
    22: ("SSH", 10),
    23: ("Telnet", 25),
    25: ("SMTP", 8),
    53: ("DNS", 5),
    80: ("HTTP", 5),
    110: ("POP3", 10),
    111: ("RPCbind", 15),
    135: ("MS-RPC", 15),
    139: ("NetBIOS", 20),
    143: ("IMAP", 10),
    443: ("HTTPS", 2),
    445: ("SMB", 25),
    993: ("IMAPS", 3),
    995: ("POP3S", 3),
    1433: ("MSSQL", 25),
    1521: ("Oracle DB", 25),
    2049: ("NFS", 20),
    3306: ("MySQL", 25),
    3389: ("RDP", 20),
    5432: ("PostgreSQL", 25),
    5900: ("VNC", 20),
    6379: ("Redis", 25),
    8080: ("HTTP-Proxy", 10),
    8443: ("HTTPS-Alt", 5),
    9200: ("Elasticsearch", 25),
    27017: ("MongoDB", 25),
}

UNKNOWN_SERVICE_WEIGHT = 3
DATABASE_PORTS = {1433, 1521, 3306, 5432, 6379, 9200, 27017}
HTTP_PORTS = {80, 8080, 8000, 8008, 8888}

# Banner içinde aranan bilinen zafiyetli sürümler: (regex, ek puan, uyarı)
CVE_SIGNATURES = [
    (re.compile(r"openssh[_ ]([4-6])\.", re.I), 30,
     "Eski OpenSSH sürümü (CVE-2016-10009 vb.). Uzaktan kod çalıştırma riski."),
    (re.compile(r"apache/2\.4\.(49|50)\b", re.I), 50,
     "Apache 2.4.49/2.4.50 Path Traversal & RCE (CVE-2021-41773 / CVE-2021-42013)."),
    (re.compile(r"vsftpd 2\.3\.4", re.I), 50,
     "vsFTPd 2.3.4 arka kapı zafiyeti (CVE-2011-2523)."),
    (re.compile(r"proftpd 1\.3\.[0-5]\b", re.I), 30,
     "Eski ProFTPD sürümü (CVE-2015-3306 mod_copy)."),
    (re.compile(r"microsoft-iis/[5-7]\.", re.I), 25,
     "Desteği bitmiş Microsoft IIS sürümü."),
]

RISK_LEVELS = [
    (25, "low", "Düşük Risk"),
    (50, "medium", "Orta Risk"),
    (75, "high", "Yüksek Risk"),
    (100, "critical", "Kritik Risk"),
]

_HOSTNAME_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.I)


def normalize_target(raw: str) -> str:
    """'https://example.com:8080/yol' gibi girdileri 'example.com' haline getirir."""
    value = raw.strip()
    if "://" in value:
        value = urlparse(value).hostname or ""
    else:
        value = value.split("/")[0]
        # IPv6 olmayan adreslerde ':port' kısmını at
        if value.count(":") == 1:
            value = value.split(":")[0]
    value = value.strip("[]").lower()

    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if not _HOSTNAME_RE.match(value):
        raise ValueError(f"Geçersiz hedef: {raw!r}")
    return value


@dataclass
class ScanResult:
    target: str
    ip: str
    open_ports: list = field(default_factory=list)
    duration: float = 0.0


class AsyncScanner:
    """Asenkron TCP connect tarayıcısı."""

    def __init__(self, target: str, ports=None, timeout: float = 1.0, concurrency: int = 300):
        self.target = normalize_target(target)
        self.ports = sorted(set(ports or COMMON_PORTS))
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(concurrency)
        self.ip = None

    async def resolve(self) -> str:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(self.target, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise LookupError(f"DNS çözümlenemedi: {self.target}") from exc
        self.ip = infos[0][4][0]
        return self.ip

    async def _grab_banner(self, reader, writer, port: int) -> str:
        try:
            if port in HTTP_PORTS:
                writer.write(f"HEAD / HTTP/1.0\r\nHost: {self.target}\r\n\r\n".encode())
                await writer.drain()
            data = await asyncio.wait_for(reader.read(1024), timeout=self.timeout)
        except (asyncio.TimeoutError, OSError):
            return ""
        text = data.decode("utf-8", errors="ignore")
        # HTTP yanıtlarında asıl bilgi 'Server:' başlığındadır
        server = re.search(r"^server:\s*(.+)$", text, re.I | re.M)
        line = server.group(1) if server else text.strip().splitlines()[0] if text.strip() else ""
        return line.strip()[:120]

    async def scan_port(self, port: int):
        async with self._semaphore:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, port), timeout=self.timeout
                )
            except (asyncio.TimeoutError, OSError):
                return None
            try:
                banner = await self._grab_banner(reader, writer, port)
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
            return {"port": port, "protocol": "TCP", "banner": banner}

    async def run(self) -> ScanResult:
        loop = asyncio.get_running_loop()
        started = loop.time()
        if self.ip is None:
            await self.resolve()
        results = await asyncio.gather(*(self.scan_port(p) for p in self.ports))
        open_ports = [r for r in results if r is not None]
        return ScanResult(self.target, self.ip, open_ports, round(loop.time() - started, 2))


def risk_level(score: int) -> dict:
    for limit, key, label in RISK_LEVELS:
        if score <= limit:
            return {"key": key, "label": label}
    return {"key": "critical", "label": "Kritik Risk"}


class RiskAnalyzer:
    """Açık port listesinden kural tabanlı risk değerlendirmesi üretir."""

    @staticmethod
    def analyze(open_ports: list, findings=()) -> dict:
        total, cve_alerts, recommendations = 0, [], []
        # Eklenti bulgularının puanı ilgili portun riskine eklenir
        plugin_weight = {}
        for f in findings:
            plugin_weight[f["port"]] = plugin_weight.get(f["port"], 0) + SEVERITY_WEIGHTS.get(f["severity"], 0)

        for item in open_ports:
            port, banner = item["port"], item.get("banner", "")
            service, weight = SERVICE_MAP.get(port, ("Bilinmiyor", UNKNOWN_SERVICE_WEIGHT))

            for pattern, extra, message in CVE_SIGNATURES:
                if pattern.search(banner):
                    weight += extra
                    cve_alerts.append(f"[Port {port}] {message}")
            weight += plugin_weight.get(port, 0)

            item["service"] = service
            item["risk"] = min(100, weight * 2)
            total += weight

            if port in DATABASE_PORTS:
                recommendations.append(f"{service} ({port}) dış ağa açık. Yalnızca iç ağdan erişilebilir olmalı, IP filtrelemesi uygulayın.")
            elif port == 23:
                recommendations.append("Telnet (23) trafiği şifresizdir. Kapatın ve yerine SSH kullanın.")
            elif port == 21:
                recommendations.append("FTP (21) kimlik bilgilerini açık metin taşır. SFTP/FTPS'e geçin.")
            elif port in (139, 445):
                recommendations.append(f"SMB/NetBIOS ({port}) internete açık olmamalı. Güvenlik duvarında engelleyin.")
            elif port in (3389, 5900):
                recommendations.append(f"Uzak masaüstü ({port}) doğrudan açık. VPN arkasına alın ve MFA kullanın.")

        if open_ports:
            recommendations.append("Kullanılmayan servisleri kapatın, yazılımları güncel tutun ve taramayı düzenli tekrarlayın.")

        score = min(100, total)
        return {
            "score": score,
            "level": risk_level(score),
            "cve_alerts": cve_alerts,
            "recommendations": list(dict.fromkeys(recommendations)),
            "ports": open_ports,
            "findings": list(findings),
        }
