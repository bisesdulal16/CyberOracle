"""
Coverage boost tests — no DB required.
Targets: routes/metrics.py (compliance/status), routes/auth.py (login).
"""

import asyncio
import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.exception_handler import secure_exception_handler

client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_rate_limit_for_these_tests():
    """Ensure rate limiting is bypassed (PYTEST=1 path) for every test here."""
    previous = os.environ.pop("DISABLE_RATE_LIMIT_TEST", None)
    yield
    if previous is not None:
        os.environ["DISABLE_RATE_LIMIT_TEST"] = previous


# ---------------------------------------------------------------------------
# /api/compliance/status — pure static return, no DB
# ---------------------------------------------------------------------------


def test_compliance_status_returns_200():
    response = client.get("/api/compliance/status")
    assert response.status_code == 200


def test_compliance_status_has_score():
    response = client.get("/api/compliance/status")
    data = response.json()
    assert "compliance_score" in data
    assert data["compliance_score"] == 0.82


def test_compliance_status_has_all_frameworks():
    response = client.get("/api/compliance/status")
    frameworks = response.json()["frameworks"]
    assert set(frameworks.keys()) == {"HIPAA", "FERPA", "NIST_CSF", "GDPR"}


def test_compliance_status_framework_fields():
    response = client.get("/api/compliance/status")
    hipaa = response.json()["frameworks"]["HIPAA"]
    assert "score" in hipaa
    assert "compliant" in hipaa
    assert "total" in hipaa


# ---------------------------------------------------------------------------
# /auth/login — in-memory user store, no DB
# ---------------------------------------------------------------------------


def test_login_valid_admin():
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "changeme_admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"


def test_login_valid_developer():
    response = client.post(
        "/auth/login", json={"username": "developer", "password": "changeme_dev"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "developer"


def test_login_valid_auditor():
    response = client.post(
        "/auth/login", json={"username": "auditor", "password": "changeme_auditor"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "auditor"


def test_login_wrong_password():
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post(
        "/auth/login", json={"username": "nobody", "password": "anything"}
    )
    assert response.status_code == 401


def test_login_returns_bearer_token_type():
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "changeme_admin"}
    )
    assert response.json()["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# /api/scan — requires JWT; covers dlp.py lines 32-33 + rbac.py lines 56-82
# ---------------------------------------------------------------------------


def _get_token(username="admin", password="changeme_admin") -> str:
    r = client.post("/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


def test_dlp_scan_with_valid_admin_token():
    token = _get_token()
    response = client.post(
        "/api/scan",
        json={"text": "My SSN is 123-45-6789"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "redacted" in response.json()


def test_dlp_scan_no_token_returns_401():
    response = client.post("/api/scan", json={"text": "hello"})
    assert response.status_code == 401


def test_dlp_scan_invalid_token_returns_401():
    response = client.post(
        "/api/scan",
        json={"text": "hello"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_dlp_scan_wrong_role_returns_403():
    token = _get_token(username="auditor", password="changeme_auditor")
    response = client.post(
        "/api/scan",
        json={"text": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# exception_handler — call directly to cover lines 9-11
# ---------------------------------------------------------------------------


def test_exception_handler_returns_500():
    request = MagicMock()
    response = asyncio.run(secure_exception_handler(request, ValueError("boom")))
    assert response.status_code == 500
