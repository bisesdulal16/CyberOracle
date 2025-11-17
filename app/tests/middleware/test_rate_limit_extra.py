from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_block_after_limit():
    for _ in range(5):
        assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 429


def test_rate_limit_resets_window():
    # Consume limit
    for _ in range(5):
        client.get("/health")

    # Wait artificially
    import time

    time.sleep(1)

    # Should work again
    assert client.get("/health").status_code == 200
