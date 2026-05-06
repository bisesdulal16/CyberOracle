"""
Log Endpoint Tests
------------------
Verifies that the /logs/ endpoint is active and protected.
Authentication required — endpoint enforces view_all_logs permission.

OWASP API1: Broken Object Level Authorization
"""

from fastapi.testclient import TestClient
from app.auth.jwt_utils import create_access_token
from app.main import app

client = TestClient(app)


def _admin_token() -> str:
    """Generate a valid admin JWT for testing."""
    return create_access_token({"sub": "admin", "role": "admin"})


def test_logs_endpoint_active():
    """
    Logs endpoint must be reachable and return active status.
    Requires a valid token with view_all_logs permission (admin role).
    """
    token = _admin_token()
    response = client.get(
        "/logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logs endpoint active"


def test_logs_endpoint_rejects_unauthenticated():
    """
    Unauthenticated requests must be rejected with 401.
    OWASP API1: Confirms endpoint is not publicly accessible.
    """
    response = client.get("/logs/")
    assert response.status_code == 401


def test_logs_endpoint_rejects_developer_role():
    """
    Developer role does not have view_all_logs permission.
    Must receive 403 Forbidden.
    """
    token = create_access_token({"sub": "developer", "role": "developer"})
    response = client.get(
        "/logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
