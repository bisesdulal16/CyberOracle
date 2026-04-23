from fastapi.testclient import TestClient
from app.auth.jwt_utils import create_access_token
from app.main import app

client = TestClient(app)


def _auth_headers(username="admin", role="admin"):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_logs_health_endpoint():
    """Logs endpoint must be reachable with valid admin auth."""
    response = client.get("/logs/", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Logs endpoint active"


def test_compliance_status_endpoint():
    response = client.get("/api/compliance/status", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "compliance_score" in data
    assert "compliant_controls" in data
    assert "non_compliant_controls" in data
    assert "total_controls" in data
    assert "frameworks" in data
    assert isinstance(data["frameworks"], dict)