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
    main.login_limiter.hits.clear()
    main.scan_limiter.hits.clear()
    main.recon_limiter.hits.clear()
    yield
