import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
from app.main import app


def _auth_headers(user_id="test-user", roles=("dev",)):
    token = create_access_token({"user_id": user_id, "roles": list(roles)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch):
    async def _noop_log_request(*args, **kwargs):
        return None

    async def _fake_route_one(prompt, model_requested, user_payload):
        return {
            "answer": f"fake response for {model_requested}",
            "model_used": model_requested,
        }

    async def _fake_route_many(prompt, models, user_payload):
        return [
            {
                "answer": f"fake response for {model}",
                "model_used": model,
            }
            for model in models
        ]

    monkeypatch.setattr("app.routes.ai.log_request", _noop_log_request)
    monkeypatch.setattr("app.routes.ai.route_one", _fake_route_one)
    monkeypatch.setattr("app.routes.ai.route_many", _fake_route_many)

    return TestClient(app)


def test_ai_query_requires_auth(client: TestClient):
    response = client.post(
        "/ai/query",
        json={"prompt": "hi", "model": "ollama:llama3"},
    )
    assert response.status_code in (401, 403)


def test_ai_query_single_model_ok(client: TestClient):
    response = client.post(
        "/ai/query",
        headers=_auth_headers(),
        json={"prompt": "Return exactly: OK", "model": "ollama:llama3"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["model_used"] == "ollama:llama3"
    assert isinstance(data.get("answer"), str)


def test_ai_query_multi_model_ok(client: TestClient):
    models = ["ollama:llama3", "ollama:mistral"]

    response = client.post(
        "/ai/query",
        headers=_auth_headers(),
        json={"prompt": "Say hi", "models": models},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["results"] is not None
    assert len(data["results"]) == len(models)
    assert [item["model_used"] for item in data["results"]] == models
