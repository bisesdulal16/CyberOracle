"""
Coverage boost tests — minimal DB dependence.
Targets:
- routes/metrics.py (compliance/status)
- routes/auth.py (login)
- routes/dlp.py (scan auth/RBAC)
- utils/exception_handler.py
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.exception_handler import secure_exception_handler

client = TestClient(app)


def _admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", "admin")


def _admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD", "changeme_admin")


def _dev_username() -> str:
    return os.getenv("DEV_USERNAME", "developer")


def _dev_password() -> str:
    return os.getenv("DEV_PASSWORD", "changeme_dev")


def _auditor_username() -> str:
    return os.getenv("AUDITOR_USERNAME", "auditor")


def _auditor_password() -> str:
    return os.getenv("AUDITOR_PASSWORD", "changeme_auditor")


@pytest.fixture(autouse=True)
def disable_rate_limit_for_these_tests():
    """Ensure rate limiting is bypassed for every test here."""
    previous = os.environ.get("PYTEST")
    os.environ["PYTEST"] = "1"
    yield
    if previous is None:
        os.environ.pop("PYTEST", None)
    else:
        os.environ["PYTEST"] = previous


def _get_token(username=None, password=None) -> str:
    username = username or _admin_username()
    password = password or _admin_password()

    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth_headers(username=None, password=None) -> dict:
    token = _get_token(username=username, password=password)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# /api/compliance/status — requires JWT
# ---------------------------------------------------------------------------


def test_compliance_status_returns_200():
    response = client.get("/api/compliance/status", headers=_auth_headers())
    assert response.status_code == 200


def test_compliance_status_has_score():
    response = client.get("/api/compliance/status", headers=_auth_headers())
    data = response.json()

    assert "compliance_score" in data
    assert isinstance(data["compliance_score"], float)
    assert 0.0 <= data["compliance_score"] <= 1.0


def test_compliance_status_has_all_frameworks():
    response = client.get("/api/compliance/status", headers=_auth_headers())
    frameworks = response.json()["frameworks"]

    assert set(frameworks.keys()) == {"HIPAA", "FERPA", "NIST_CSF", "GDPR"}


def test_compliance_status_framework_fields():
    response = client.get("/api/compliance/status", headers=_auth_headers())
    hipaa = response.json()["frameworks"]["HIPAA"]

    assert "score" in hipaa
    assert "status" in hipaa
    assert "compliant" in hipaa
    assert "total" in hipaa


# ---------------------------------------------------------------------------
# /auth/login — in-memory/env-backed user store
# ---------------------------------------------------------------------------


def test_login_valid_admin():
    response = client.post(
        "/auth/login",
        json={"username": _admin_username(), "password": _admin_password()},
    )
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"


def test_login_valid_developer():
    response = client.post(
        "/auth/login",
        json={"username": _dev_username(), "password": _dev_password()},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "developer"


def test_login_valid_auditor():
    response = client.post(
        "/auth/login",
        json={"username": _auditor_username(), "password": _auditor_password()},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "auditor"


def test_login_wrong_password():
    response = client.post(
        "/auth/login",
        json={"username": _admin_username(), "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post(
        "/auth/login",
        json={"username": "nobody", "password": "anything"},
    )
    assert response.status_code == 401


def test_login_returns_bearer_token_type():
    response = client.post(
        "/auth/login",
        json={"username": _admin_username(), "password": _admin_password()},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


# ---------------------------------------------------------------------------
# /api/scan — requires JWT; admin/developer allowed, auditor forbidden
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# /api/scan — requires JWT; admin/developer allowed, auditor forbidden
# ---------------------------------------------------------------------------


def test_dlp_scan_with_valid_admin_token(monkeypatch):
    from unittest.mock import AsyncMock
    import app.routes.dlp as dlp_module

    monkeypatch.setattr(dlp_module, "log_request", AsyncMock())

    token = _get_token()
    # Patch log_request to avoid asyncpg concurrent-operation errors in the
    # synchronous TestClient context (the real DB call is covered elsewhere).
    with patch("app.routes.dlp.log_request", new_callable=AsyncMock):
        response = client.post(
            "/api/scan",
            json={"text": "My SSN is 123-45-6789"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert "redacted" in response.json()


def test_dlp_scan_no_token_returns_401(monkeypatch):
    from unittest.mock import AsyncMock
    import app.routes.dlp as dlp_module

    monkeypatch.setattr(dlp_module, "log_request", AsyncMock())

    response = client.post("/api/scan", json={"text": "hello"})
    assert response.status_code == 401


def test_dlp_scan_invalid_token_returns_401(monkeypatch):
    from unittest.mock import AsyncMock
    import app.routes.dlp as dlp_module

    monkeypatch.setattr(dlp_module, "log_request", AsyncMock())

    response = client.post(
        "/api/scan",
        json={"text": "hello"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_dlp_scan_wrong_role_returns_403(monkeypatch):
    from unittest.mock import AsyncMock
    import app.routes.dlp as dlp_module

    monkeypatch.setattr(dlp_module, "log_request", AsyncMock())

    token = _get_token(
        username=_auditor_username(),
        password=_auditor_password(),
    )
    response = client.post(
        "/api/scan",
        json={"text": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# exception_handler — direct call
# ---------------------------------------------------------------------------


def test_exception_handler_returns_500():
    request = MagicMock()
    response = asyncio.run(secure_exception_handler(request, ValueError("boom")))
    assert response.status_code == 500
