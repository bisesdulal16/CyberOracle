# tests/routes/test_ai_route.py

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.ai as ai_module
from app.auth.jwt_utils import create_access_token
from app.services.dlp_engine import PolicyDecision


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "test", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    """
    Minimal FastAPI app that mounts only the AI router.
    """
    app = FastAPI()
    app.include_router(ai_module.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def patch_log_request(monkeypatch):
    """
    Patch log_request used inside app.routes.ai so tests don't depend
    on the real logging / DB / anyio behavior.
    """

    async def _log_request(**kwargs):
        return None

    monkeypatch.setattr(ai_module, "log_request", _log_request)


def test_ai_query_options_endpoints(client):
    r1 = client.options("/ai/query")
    assert r1.status_code == 200

    r2 = client.options("/ai/query/")
    assert r2.status_code == 200


def test_ai_query_happy_path(client, auth_headers, monkeypatch):
    """
    DLP allows input and output — model returns safe string.
    """

    async def fake_route_one(prompt, model, user):
        assert "hello" in prompt.lower()
        return {"answer": "Safe model response", "model_used": "ollama:llama3.2:1b"}

    monkeypatch.setattr(ai_module.model_router, "route_one", fake_route_one)

    response = client.post(
        "/ai/query",
        json={"prompt": "Hello, nothing sensitive here."},
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["model"] is not None  # model name varies by environment
    assert data["output"]["blocked"] is False
    assert isinstance(data["output"]["text"], str)
    assert "request_id" in data
    assert "security" in data
    assert "meta" in data


def test_ai_query_blocks_on_input_dlp(client, auth_headers, monkeypatch):
    """
    Force input DLP to BLOCK — no model call should be made.
    """

    class FakeFinding:
        def __init__(self, type_: str):
            self.type = type_

    def fake_scan_text(text: str):
        return text, [FakeFinding("test_sensitive")]

    class FakeDecision:
        def __init__(self, decision, risk_score: int):
            self.decision = decision
            self.risk_score = risk_score

    def fake_decide(findings):
        return FakeDecision(PolicyDecision.BLOCK, risk_score=90)

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)

    async def fake_route_one(prompt, model, user):
        raise AssertionError("Model should not be called when input is blocked")

    monkeypatch.setattr(ai_module.model_router, "route_one", fake_route_one)

    response = client.post(
        "/ai/query", json={"prompt": "This should be blocked"}, headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["output"]["blocked"] is True
    assert data["output"]["redacted"] is False
    assert data["output"]["text"] == "Request blocked by DLP policy."
    assert data["security"]["policy_decision"] == "block"
    assert data["security"]["phase"] == "input"


def test_ai_query_model_error_returns_502(client, auth_headers, monkeypatch):
    """
    model_router.route_one raises an exception.
    Route must return HTTP 502 with a safe generic message.
    Internal error details must NOT be exposed (NCFR6).
    """

    async def fake_route_one(prompt, model, user):
        raise RuntimeError("model backend is down")

    monkeypatch.setattr(ai_module.model_router, "route_one", fake_route_one)

    response = client.post(
        "/ai/query", json={"prompt": "Hello, world!"}, headers=auth_headers
    )
    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    # NCFR6: Must NOT expose internal error details like repr(e)
    assert "RuntimeError" not in data["detail"]
    assert "model backend is down" not in data["detail"]
    # Must be a safe generic message
    assert (
        "unavailable" in data["detail"].lower() or "try again" in data["detail"].lower()
    )


def test_ai_query_blocks_on_output_dlp(client, auth_headers, monkeypatch):
    """
    Input passes DLP but output is BLOCKED.
    """

    class FakeFinding:
        def __init__(self, type_: str):
            self.type = type_

    def fake_scan_text(text: str):
        if "trigger-output-block" in text:
            return text, [FakeFinding("output_sensitive")]
        return text, []

    class FakeDecision:
        def __init__(self, decision, risk_score: int):
            self.decision = decision
            self.risk_score = risk_score

    def fake_decide(findings):
        if findings:
            return FakeDecision(PolicyDecision.BLOCK, risk_score=80)
        return FakeDecision(PolicyDecision.ALLOW, risk_score=0)

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)

    async def fake_route_one(prompt, model, user):
        return {
            "answer": "this will trigger-output-block in DLP",
            "model_used": "ollama:test",
        }

    monkeypatch.setattr(ai_module.model_router, "route_one", fake_route_one)

    response = client.post(
        "/ai/query", json={"prompt": "Safe input"}, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["output"]["blocked"] is True
    assert data["output"]["text"] == "Response blocked by DLP policy."
    assert data["security"]["policy_decision"] == "block"
    assert (
        data["security"]["blocked_reason"] == "Sensitive data detected in model output."
    )
    assert data["security"]["phase"] == "output"


def test_ai_query_redacts_output_dlp(client, auth_headers, monkeypatch):
    """
    Input passes DLP but output is REDACTED.
    """

    class FakeFinding:
        def __init__(self, type_: str):
            self.type = type_

    def fake_scan_text(text: str):
        if "trigger-output-redact" in text:
            return text, [FakeFinding("output_sensitive")]
        return text, []

    class FakeDecision:
        def __init__(self, decision, risk_score: int):
            self.decision = decision
            self.risk_score = risk_score

    def fake_decide(findings):
        if findings:
            return FakeDecision(PolicyDecision.REDACT, risk_score=50)
        return FakeDecision(PolicyDecision.ALLOW, risk_score=0)

    def fake_redact_text(text, findings):
        return "REDACTED_TEXT", [{"rule": f.type} for f in findings]

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)
    monkeypatch.setattr(ai_module.dlp_engine, "redact_text", fake_redact_text)

    async def fake_route_one(prompt, model, user):
        return {
            "answer": "this will trigger-output-redact in DLP",
            "model_used": "ollama:test",
        }

    monkeypatch.setattr(ai_module.model_router, "route_one", fake_route_one)

    response = client.post(
        "/ai/query", json={"prompt": "Safe input"}, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["output"]["blocked"] is False
    assert data["output"]["redacted"] is True
    assert data["output"]["text"] == "REDACTED_TEXT"
    assert data["security"]["policy_decision"] == "redact"
    assert data["security"]["redactions"] != []
