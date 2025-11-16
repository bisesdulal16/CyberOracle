from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_logs_endpoint_active():
    response = client.get("/logs/")
    assert response.status_code == 200
    assert response.json()["message"] == "Logs endpoint active"
