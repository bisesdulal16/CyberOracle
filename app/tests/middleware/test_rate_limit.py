from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rate_limiting():
    # first 5 requests allowed
    for _ in range(5):
        assert client.get("/health").status_code == 200

    # 6th should be blocked
    assert client.get("/health").status_code == 429
