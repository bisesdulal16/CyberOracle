from app.main import app
from starlette.testclient import TestClient

client = TestClient(app)


def test_block_ssn():
    body = {"text": "My SSN is 123-45-6789"}
    res = client.post("/api/analyze", json=body)
    assert res.status_code == 400


def test_allow_clean_text():
    body = {"text": "Hello world"}
    res = client.post("/api/analyze", json=body)
    assert res.status_code == 200
