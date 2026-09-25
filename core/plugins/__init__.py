"""
ReconClaw eklenti sistemi.

Her eklenti, bu paketteki bir modülde tanımlanan ve `Plugin` sınıfından türeyen
bir sınıftır. Tarama bittikten sonra, eklentinin ilgilendiği açık portlar için
`check()` çağrılır ve dönen bulgular risk skoruna eklenir.

Hangi eklentilerin çalışacağı proje kökündeki `plugins` dosyasından okunur.
Yeni bir eklenti yazmak için:
  1. core/plugins/ altına bir modül ekleyin ve içinde Plugin'den türeyen bir sınıf tanımlayın
  2. Sınıfın `name` değerini `plugins` dosyasına yeni bir satır olarak yazın
"""

import asyncio
import importlib
import os
import pkgutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "plugins")

# Bulgu şiddeti -> risk skoruna eklenen puan
SEVERITY_WEIGHTS = {"info": 0, "low": 3, "medium": 8, "high": 15}


class Plugin:
    name = ""
    description = ""
    ports = set()  # Eklentinin çalışacağı portlar

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    def finding(self, port, severity, title, detail=""):
        return {"plugin": self.name, "port": port, "severity": severity, "title": title, "detail": detail}

    async def check(self, target: str, ip: str, port: int) -> list:
        raise NotImplementedError


def available_plugins() -> dict:
    """Paketteki tüm eklenti sınıflarını {ad: sınıf} olarak döndürür."""
    found = {}
    for module in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{module.name}")
        for obj in vars(mod).values():
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin and obj.name:
                found[obj.name] = obj
    return found


def enabled_names(path: str = CONFIG_PATH) -> list:
    """`plugins` dosyasındaki etkin eklenti adlarını okur (# ile başlayan satırlar yorumdur)."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = [line.split("#", 1)[0].strip() for line in fh]
    except FileNotFoundError:
        return []
    return [line for line in lines if line]


async def run_plugins(target: str, ip: str, open_ports: list, timeout: float = 3.0, names=None) -> list:
    """Etkin eklentileri ilgili açık portlarda eşzamanlı çalıştırır ve bulguları döndürür."""
    registry = available_plugins()
    plugins = [registry[n](timeout) for n in (names if names is not None else enabled_names()) if n in registry]

    jobs = [
        plugin.check(target, ip, item["port"])
        for plugin in plugins
        for item in open_ports
        if item["port"] in plugin.ports
    ]
    results = await asyncio.gather(*jobs, return_exceptions=True)
    # Bir eklentinin hata vermesi taramanın geri kalanını bozmamalı
    return [f for r in results if isinstance(r, list) for f in r]
