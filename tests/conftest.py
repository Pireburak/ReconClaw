import pytest


@pytest.fixture(autouse=True)
def reset_rate_limits():
    # İstek sınırlayıcılar süreç genelindedir; testler birbirini etkilemesin
    try:
        import main
    except ImportError:
        yield
        return
    main.login_limiter.hits.clear()
    main.scan_limiter.hits.clear()
    yield
