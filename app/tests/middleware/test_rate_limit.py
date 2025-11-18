import os
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)
os.environ["DISABLE_RATE_LIMIT_TEST"] = "1"


def test_rate_limiting():
    # Allow first 5
    for _ in range(5):
        assert client.get("/health").status_code == 200

    # 6th blocked
    assert client.get("/health").status_code == 429
