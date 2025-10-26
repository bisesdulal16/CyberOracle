from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Ensure the /health endpoint returns status OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK", "service": "CyberOracle API"}
