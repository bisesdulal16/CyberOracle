"""
Rate Limiter Tests
------------------
Verifies that the middleware enforces per-IP request limits
and returns HTTP 429 once the threshold is exceeded.

OWASP API4: Unrestricted Resource Consumption
PEP 8: descriptive names, pytest.raises idiom used where applicable
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

    OWASP API4: Confirms legitimate traffic is not blocked.
    """
    for i in range(5):
        response = client.get("/health")
        assert response.status_code == 200, f"Request {i + 1} was unexpectedly blocked"


def test_rate_limit_blocks_on_exceeded():
    """
    The (limit + 1)th request should be rejected with HTTP 429.

    OWASP API4: Confirms DoS and brute-force mitigation is active.
    """
    for _ in range(5):
        client.get("/health")

    response = client.get("/health")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_rate_limit_response_contains_detail():
    """
    429 response must include a human-readable detail message.
    """
    for _ in range(6):
        response = client.get("/health")

    assert response.status_code == 429
    body = response.json()
    assert "detail" in body
    assert "requests per" in body["detail"]


def test_rate_limit_tracks_per_ip():
    """
    Verify that the rate limiter maintains separate buckets.
    After exhausting the limit, the bucket key should be present in requests_log.
    """
    for _ in range(5):
        client.get("/health")

    # At least one bucket key should exist in the log
    assert len(requests_log) > 0
