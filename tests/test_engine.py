import asyncio

import pytest

from core.engine import AsyncScanner, RiskAnalyzer, normalize_target, risk_level


@pytest.mark.parametrize("raw, expected", [
    ("example.com", "example.com"),
    ("  Example.COM  ", "example.com"),
    ("https://example.com/login?x=1", "example.com"),
    ("http://example.com:8080", "example.com"),
    ("example.com:22", "example.com"),
    ("192.168.1.10", "192.168.1.10"),
])
def test_normalize_target(raw, expected):
    assert normalize_target(raw) == expected


@pytest.mark.parametrize("raw", ["", "exa mple.com", "-bad-.com", "<script>"])
def test_normalize_target_rejects_invalid(raw):
    with pytest.raises(ValueError):
        normalize_target(raw)


@pytest.mark.parametrize("score, key", [(0, "low"), (25, "low"), (26, "medium"), (60, "high"), (76, "critical")])
def test_risk_level_boundaries(score, key):
    assert risk_level(score)["key"] == key


def test_analyzer_scores_and_detects_cve():
    ports = [
        {"port": 22, "protocol": "TCP", "banner": "SSH-2.0-OpenSSH_5.3"},
        {"port": 3306, "protocol": "TCP", "banner": ""},
    ]
    result = RiskAnalyzer.analyze(ports)

    assert result["score"] == 65  # SSH 10 + eski OpenSSH 30 + MySQL 25
    assert result["level"]["key"] == "high"
    assert any("OpenSSH" in a for a in result["cve_alerts"])
    assert any("MySQL" in r for r in result["recommendations"])
    assert [p["service"] for p in result["ports"]] == ["SSH", "MySQL"]


def test_analyzer_empty():
    result = RiskAnalyzer.analyze([])
    assert result["score"] == 0
    assert result["recommendations"] == []


def test_scanner_finds_open_port_and_banner():
    async def scenario():
        async def handler(reader, writer):
            writer.write(b"SSH-2.0-TestServer\r\n")
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            scanner = AsyncScanner("127.0.0.1", ports=[port], timeout=1.0)
            return port, await scanner.run()

    port, result = asyncio.run(scenario())
    assert result.ip == "127.0.0.1"
    assert result.open_ports == [{"port": port, "protocol": "TCP", "banner": "SSH-2.0-TestServer"}]
