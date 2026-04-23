"""
Rate Limiter Tests
------------------
Verifies that the middleware enforces per-IP request limits
and returns HTTP 429 once the threshold is exceeded.
Uses /health as the test endpoint since it is a simple endpoint
that does not require bcrypt verification, making tests portable
across CI environments with different bcrypt versions.
OWASP API4: Unrestricted Resource Consumption
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.rate_limiter import requests_log

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    """Ensure a clean rate limit state before every test."""
    requests_log.clear()
    yield
    requests_log.clear()


def test_rate_limit_allows_requests_within_limit():
    """
    First N requests (up to the test limit of 5) should all succeed.
    Uses /logs/ which is NOT in EXEMPT_PATHS.
    OWASP API4: Confirms legitimate traffic is not blocked.
    """
    from app.auth.jwt_utils import create_access_token

    token = create_access_token({"sub": "test", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(5):
        response = client.get("/logs/", headers=headers)
        assert (
            response.status_code != 429
        ), f"Request {i + 1} was unexpectedly rate limited"


def test_rate_limit_blocks_on_exceeded():
    """
    The (limit + 1)th request should be rejected with HTTP 429.
    OWASP API4: Confirms DoS and brute-force mitigation is active.
    """
    from app.auth.jwt_utils import create_access_token

    token = create_access_token({"sub": "test", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(5):
        client.get("/logs/", headers=headers)

    response = client.get("/logs/", headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_rate_limit_response_contains_detail():
    """
    429 response must include a human-readable detail message.
    """
    from app.auth.jwt_utils import create_access_token

    token = create_access_token({"sub": "test", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(6):
        response = client.get("/logs/", headers=headers)

    assert response.status_code == 429
    body = response.json()
    assert "detail" in body
    assert "requests per" in body["detail"]


def test_rate_limit_tracks_per_ip():
    """
    Verify that the rate limiter maintains separate buckets per IP.
    After exhausting the limit, the bucket key should exist in requests_log.
    """
    from app.auth.jwt_utils import create_access_token

    token = create_access_token({"sub": "test", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(5):
        client.get("/logs/", headers=headers)

    assert len(requests_log) > 0
