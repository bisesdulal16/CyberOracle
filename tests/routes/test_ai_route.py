# app/tests/routes/test_ai_route.py

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.ai as ai_module
from app.services.dlp_engine import PolicyDecision


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
        # no-op for tests
        return None

    # log_request is imported into ai_module, so patch there
    monkeypatch.setattr(ai_module, "log_request", _log_request)


def test_ai_query_options_endpoints(client):
    # /ai/query (no trailing slash)
    r1 = client.options("/ai/query")
    assert r1.status_code == 200

    # /ai/query/ (with trailing slash)
    r2 = client.options("/ai/query/")
    assert r2.status_code == 200


def test_ai_query_happy_path(client, monkeypatch):
    """
    - DLP allows input and output
    - OllamaClient returns a safe string
    - Should not be blocked or heavily redacted
    """

    class FakeOllamaClient:
        async def generate(self, model: str, prompt: str) -> str:
            # The route forces this model name
            assert model == "llama3:latest"
            assert "hello" in prompt.lower()
            return "Safe model response"

    monkeypatch.setattr(ai_module, "OllamaClient", lambda: FakeOllamaClient())

    # Let the real DLP engine run; with a harmless prompt it should ALLOW
    response = client.post(
        "/ai/query", json={"prompt": "Hello, nothing sensitive here."}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "llama3:latest"
    assert data["output"]["blocked"] is False
    # We don't over-assert the exact text, just basic shape
    assert isinstance(data["output"]["text"], str)
    assert "request_id" in data
    assert "security" in data
    assert "meta" in data


def test_ai_query_blocks_on_input_dlp(client, monkeypatch):
    """
    Force the input DLP to BLOCK so we exercise the early-return branch.
    No model call should be made.
    """

    class FakeFinding:
        def __init__(self, type_: str):
            self.type = type_

    def fake_scan_text(text: str):
        # Pretend we detected something sensitive in the input
        return text, [FakeFinding("test_sensitive")]

    class FakeDecision:
        def __init__(self, decision, risk_score: int):
            self.decision = decision
            self.risk_score = risk_score

    def fake_decide(findings):
        # Always BLOCK when there are findings
        return FakeDecision(PolicyDecision.BLOCK, risk_score=90)

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)

    # If the model gets called here, something is wrong
    class FakeOllamaClient:
        async def generate(self, model: str, prompt: str) -> str:
            raise AssertionError("Model should not be called when input is blocked")

    monkeypatch.setattr(ai_module, "OllamaClient", lambda: FakeOllamaClient())

    response = client.post("/ai/query", json={"prompt": "This should be blocked"})
    assert response.status_code == 200

    data = response.json()
    assert data["output"]["blocked"] is True
    assert data["output"]["redacted"] is False
    assert data["output"]["text"] == "Request blocked by DLP policy."
    assert data["security"]["policy_decision"] == "block"
    assert data["security"]["phase"] == "input"


def test_ai_query_model_error_returns_502(client, monkeypatch):
    """
    Exercise the error-handling branch:
    - OllamaClient.generate raises an exception
    - Route should translate it into HTTP 502
    """

    class FailingOllamaClient:
        async def generate(self, model: str, prompt: str) -> str:
            raise RuntimeError("model backend is down")

    monkeypatch.setattr(ai_module, "OllamaClient", lambda: FailingOllamaClient())

    response = client.post("/ai/query", json={"prompt": "Hello, world!"})
    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "RuntimeError" in data["detail"]


def test_ai_query_blocks_on_output_dlp(client, monkeypatch):
    """
    Input passes DLP, but the *output* is blocked.
    This hits the output BLOCK branch.
    """

    class FakeFinding:
        def __init__(self, type_: str):
            self.type = type_

    def fake_scan_text(text: str):
        # Only treat model output as sensitive
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
        # Assume ALLOW exists as the non-blocking default
        return FakeDecision(PolicyDecision.ALLOW, risk_score=0)

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)

    class FakeOllamaClient:
        async def generate(self, model: str, prompt: str) -> str:
            # This string will cause the *output* DLP to block
            return "this will trigger-output-block in DLP"

    monkeypatch.setattr(ai_module, "OllamaClient", lambda: FakeOllamaClient())

    response = client.post("/ai/query", json={"prompt": "Safe input"})
    assert response.status_code == 200
    data = response.json()

    assert data["output"]["blocked"] is True
    assert data["output"]["text"] == "Response blocked by DLP policy."
    assert data["security"]["policy_decision"] == "block"
    assert (
        data["security"]["blocked_reason"] == "Sensitive data detected in model output."
    )
    assert data["security"]["phase"] == "output"


def test_ai_query_redacts_output_dlp(client, monkeypatch):
    """
    Input passes DLP, but output is REDACTED (not fully blocked).
    Exercises the REDACT branch and the call to dlp_engine.redact_text.
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
        # Simulate redaction + return some metadata
        return "REDACTED_TEXT", [{"rule": f.type} for f in findings]

    monkeypatch.setattr(ai_module.dlp_engine, "scan_text", fake_scan_text)
    monkeypatch.setattr(ai_module.dlp_engine, "decide", fake_decide)
    monkeypatch.setattr(ai_module.dlp_engine, "redact_text", fake_redact_text)

    class FakeOllamaClient:
        async def generate(self, model: str, prompt: str) -> str:
            return "this will trigger-output-redact in DLP"

    monkeypatch.setattr(ai_module, "OllamaClient", lambda: FakeOllamaClient())

    response = client.post("/ai/query", json={"prompt": "Safe input"})
    assert response.status_code == 200
    data = response.json()

    assert data["output"]["blocked"] is False
    assert data["output"]["redacted"] is True
    assert data["output"]["text"] == "REDACTED_TEXT"
    assert data["security"]["policy_decision"] == "redact"
    assert data["security"]["redactions"] != []
