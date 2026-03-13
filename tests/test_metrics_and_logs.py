from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_logs_health_endpoint():
    response = client.get("/logs/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert data["message"] == "Logs endpoint active"


def test_compliance_status_endpoint():
    response = client.get("/api/compliance/status")
    assert response.status_code == 200

    data = response.json()
    assert "compliance_score" in data
    assert "compliant_controls" in data
    assert "non_compliant_controls" in data
    assert "total_controls" in data
    assert "frameworks" in data
    assert isinstance(data["frameworks"], dict)