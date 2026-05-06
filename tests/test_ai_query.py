import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
from app.main import app


def _auth_headers(username="test-user", role="developer"):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(monkeypatch):
    async def _noop_log_request(*args, **kwargs):
        return None

    monkeypatch.setattr("app.routes.ai.log_request", _noop_log_request)

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

    assert response.status_code in (200, 500, 502)

    data = response.json()
    assert isinstance(data, dict)

    if response.status_code == 200:
        assert "request_id" in data
        assert data["model"] == "ollama:llama3"
        assert "output" in data
        assert "security" in data
        assert "meta" in data
        assert isinstance(data["output"].get("text"), str)
        assert isinstance(data["output"].get("redacted"), bool)
        assert isinstance(data["output"].get("blocked"), bool)
    else:
        assert "detail" in data or "error" in data


def test_ai_query_model_field_accepted(client: TestClient):
    response = client.post(
        "/ai/query",
        headers=_auth_headers(),
        json={"prompt": "Say hi", "model": "ollama:mistral"},
    )

    assert response.status_code in (200, 500, 502)

    data = response.json()
    assert isinstance(data, dict)

    if response.status_code == 200:
        assert data["model"] == "ollama:mistral"
        assert "output" in data
        assert "security" in data
        assert "meta" in data
    else:
        assert "detail" in data or "error" in data
