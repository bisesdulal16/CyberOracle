# tests/test_ai_query.py
import pytest, os
from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt_utils import create_access_token

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="DB integration tests disabled. Run with RUN_DB_TESTS=1 and Postgres up."
)

def _auth_headers(user_id="test-user", roles=("dev",)):
    token = create_access_token({"user_id": user_id, "roles": list(roles)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def client(monkeypatch):
    # ✅ patch the reference used inside app.routes.ai
    async def _noop_log_request(*args, **kwargs):
        return None

    monkeypatch.setattr("app.routes.ai.log_request", _noop_log_request)

    return TestClient(app)

def test_ai_query_requires_auth(client: TestClient):
    r = client.post("/ai/query", json={"prompt": "hi", "model": "ollama:llama3"})
    assert r.status_code in (401, 403)

def test_ai_query_single_model_ok(client: TestClient):
    r = client.post(
        "/ai/query",
        headers=_auth_headers(),
        json={"prompt": "Return exactly: OK", "model": "ollama:llama3"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["model_used"] == "ollama:llama3"
    assert isinstance(data.get("answer"), str)

def test_ai_query_multi_model_ok(client: TestClient):
    models = ["ollama:llama3", "ollama:mistral"]
    r = client.post(
        "/ai/query",
        headers=_auth_headers(),
        json={"prompt": "Say hi", "models": models},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["results"] is not None
    assert len(data["results"]) == len(models)
    assert [x["model_used"] for x in data["results"]] == models
