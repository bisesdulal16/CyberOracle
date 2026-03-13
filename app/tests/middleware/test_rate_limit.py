from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rate_limiting(monkeypatch):
    monkeypatch.setenv("ENABLE_RATE_LIMIT_TEST", "1")

    # clear shared state before test
    from app.middleware.rate_limiter import requests_log

    requests_log.clear()

    # Allow first 5
    for _ in range(5):
        assert client.get("/health").status_code == 200

    # 6th blocked
    assert client.get("/health").status_code == 429
