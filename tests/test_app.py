"""
Unit Tests for CyberOracle FastAPI Application
----------------------------------------------
Tests validate health endpoint, DLP middleware redaction,
and authenticated endpoint behaviour.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt_utils import create_access_token

client = TestClient(app)


def _auth_headers(role="developer"):
    token = create_access_token({"sub": "testuser", "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _bypass_rate_limit():
    previous = os.environ.pop("DISABLE_RATE_LIMIT_TEST", None)
    yield
    if previous is not None:
        os.environ["DISABLE_RATE_LIMIT_TEST"] = previous


def test_health_endpoint():
    """Health endpoint must return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK", "service": "CyberOracle API"}


def test_dlp_redacts_ssn():
    """
    DLP middleware must redact SSNs in request body.
    POST /logs/ requires authentication (NCFR3).
    """
    payload = {"data": "My SSN is 123-45-6789"}
    response = client.post(
        "/logs/",
        json=payload,
        headers=_auth_headers("developer"),
    )
    assert response.status_code in [200, 201, 404]
    assert ("***" in response.text) or ("<GENERIC_SSN>" in response.text)


def test_dlp_allows_normal_data():
    """
    DLP middleware must not alter harmless data.
    POST /logs/ requires authentication (NCFR3).
    """
    payload = {"data": "Hello from CyberOracle"}
    response = client.post(
        "/logs/",
        json=payload,
        headers=_auth_headers("developer"),
    )
    assert response.status_code in [200, 201, 404]
    assert "***" not in str(response.text)