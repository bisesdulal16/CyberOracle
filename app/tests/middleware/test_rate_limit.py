from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.middleware.rate_limiter import requests_log

# Prevent TestClient from throwing HTTPException directly
client = TestClient(app, raise_server_exceptions=False)

# Fixture to clear the state before every test
@pytest.fixture(autouse=True)
def cleanup_rate_limit_log():
    # Clear the dictionary before running the test
    requests_log.clear()

def test_rate_limiting():
    # This loop ensures the log count is 5 for the test client IP
    for i in range(5):
        r = client.get("/health")
        assert r.status_code == 200

    r = client.get("/health")
    assert r.status_code == 429
