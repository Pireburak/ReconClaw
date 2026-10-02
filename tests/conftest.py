import pytest


@pytest.fixture(autouse=True)
def reset_rate_limits(monkeypatch):
    # İstek sınırlayıcılar süreç genelindedir; testler birbirini etkilemesin
    try:
        import main
    except ImportError:
        yield
        return
    from core import config

    # Testlerde arka plan izleme zamanlayıcısı çalışmasın (izleme testleri görevleri elle tetikler)
    monkeypatch.setattr(config, "SCHEDULER_ENABLED", False)
    # Testlerde GeoIP ve kur servislerine çıkılmasın (yedek kurlar kullanılır)
    from core import pricing

    async def no_refresh(force=False):
        return pricing._rates

    monkeypatch.setattr(config, "GEO_LOOKUP", False)
    monkeypatch.setattr(pricing, "refresh_rates", no_refresh)
    main.login_limiter.hits.clear()
    main.scan_limiter.hits.clear()
    main.recon_limiter.hits.clear()
    yield
