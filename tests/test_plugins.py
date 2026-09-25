import asyncio
import shutil
import socket
import ssl
import subprocess

import pytest

from core.engine import RiskAnalyzer
from core.plugins import available_plugins, enabled_names, run_plugins
from core.plugins.http_headers import HttpHeadersPlugin
from core.plugins.tls_cert import TlsCertPlugin


def serve(handler, ssl_ctx=None):
    """Rastgele bir portta geçici sunucu açar, (sunucu, port) döndürür."""
    async def start():
        server = await asyncio.start_server(handler, "127.0.0.1", 0, ssl=ssl_ctx)
        return server, server.sockets[0].getsockname()[1]
    return start()


def http_handler(response: bytes):
    async def handler(reader, writer):
        await reader.read(1024)
        writer.write(response)
        await writer.drain()
        writer.close()
    return handler


def test_registry_and_config(tmp_path):
    assert {"http_headers", "tls_cert"} <= set(available_plugins())

    cfg = tmp_path / "plugins"
    cfg.write_text("# yorum\nhttp_headers\n\n# tls_cert\n", encoding="utf-8")
    assert enabled_names(str(cfg)) == ["http_headers"]
    assert enabled_names(str(tmp_path / "yok")) == []


def test_http_headers_reports_missing_headers_and_version_leak():
    response = b"HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\nX-Frame-Options: DENY\r\n\r\n<html>"

    async def scenario():
        server, port = await serve(http_handler(response))
        async with server:
            plugin = HttpHeadersPlugin(timeout=2)
            plugin.ports = {port}
            return await plugin.check("localhost", "127.0.0.1", port)

    titles = {f["title"] for f in asyncio.run(scenario())}
    assert "Eksik başlık: content-security-policy" in titles
    assert "Eksik başlık: x-content-type-options" in titles
    assert "Eksik başlık: x-frame-options" not in titles
    assert "Sürüm ifşası: server: nginx/1.18.0" in titles


def test_http_headers_ignores_non_http_service():
    async def scenario():
        server, port = await serve(http_handler(b"SSH-2.0-OpenSSH_9.0\r\n"))
        async with server:
            return await HttpHeadersPlugin(timeout=2).check("localhost", "127.0.0.1", port)

    assert asyncio.run(scenario()) == []


def test_run_plugins_only_matching_ports_and_survives_errors(monkeypatch):
    # Boş bir port bul: kimse dinlemediği için bağlantı hatası alınacak
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        closed_port = sock.getsockname()[1]
    monkeypatch.setattr(HttpHeadersPlugin, "ports", {closed_port})

    findings = asyncio.run(run_plugins("localhost", "127.0.0.1", [{"port": closed_port}, {"port": 22}],
                                       timeout=0.5, names=["http_headers", "olmayan"]))
    assert findings == []


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl bulunamadı")
def test_tls_cert_flags_self_signed(tmp_path):
    key, cert = tmp_path / "key.pem", tmp_path / "cert.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "10",
                    "-subj", "/CN=localhost", "-keyout", str(key), "-out", str(cert)],
                   check=True, capture_output=True)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)

    async def handler(reader, writer):
        writer.close()

    async def scenario():
        server, port = await serve(handler, ctx)
        async with server:
            return await TlsCertPlugin(timeout=2).check("localhost", "127.0.0.1", port)

    findings = asyncio.run(scenario())
    assert findings[0]["severity"] == "high"
    assert findings[0]["title"] == "Sertifika doğrulanamadı"
    assert "self-signed" in findings[0]["detail"] or "self signed" in findings[0]["detail"]


def test_analyzer_adds_plugin_findings_to_port_risk():
    ports = [{"port": 443, "protocol": "TCP", "banner": ""}]
    findings = [
        {"plugin": "tls_cert", "port": 443, "severity": "high", "title": "x", "detail": ""},
        {"plugin": "http_headers", "port": 443, "severity": "medium", "title": "y", "detail": ""},
        {"plugin": "tls_cert", "port": 443, "severity": "info", "title": "z", "detail": ""},
    ]
    result = RiskAnalyzer.analyze(ports, findings)
    assert result["score"] == 2 + 15 + 8
    assert result["ports"][0]["risk"] == 50
    assert result["findings"] == findings
