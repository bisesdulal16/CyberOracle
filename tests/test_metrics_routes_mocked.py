from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.metrics as metrics_module


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class FakeEntriesResult:
    def __init__(self, entries):
        self._entries = entries

    def scalars(self):
        return self

    def all(self):
        return self._entries


class FakeSession:
    def __init__(self, execute_results):
        self._execute_results = execute_results
        self._index = 0

    async def execute(self, query):
        result = self._execute_results[self._index]
        self._index += 1
        return result


class FakeSessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def build_client():
    app = FastAPI()
    app.include_router(metrics_module.router)
    return TestClient(app)


def test_metrics_summary_endpoint(monkeypatch):
    fake_session = FakeSession(
        [
            FakeScalarResult(12),  # total_prompts_24h
            FakeScalarResult(3),   # blocked_prompts
            FakeScalarResult(2),   # redacted_outputs
            FakeScalarResult(1),   # high_risk_events
        ]
    )

    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get("/api/metrics/summary")

    assert response.status_code == 200
    data = response.json()

    assert data["total_prompts_24h"] == 12
    assert data["blocked_prompts"] == 3
    assert data["redacted_outputs"] == 2
    assert data["high_risk_events"] == 1
    assert data["active_models"] == 1


def test_compliance_status_endpoint():
    client = build_client()
    response = client.get("/api/compliance/status")

    assert response.status_code == 200
    data = response.json()

    assert data["compliance_score"] == 0.82
    assert data["compliant_controls"] == 41
    assert data["non_compliant_controls"] == 9
    assert data["total_controls"] == 50
    assert "frameworks" in data
    assert "HIPAA" in data["frameworks"]
    assert "FERPA" in data["frameworks"]
    assert "NIST_CSF" in data["frameworks"]
    assert "GDPR" in data["frameworks"]


def test_recent_alerts_endpoint_with_entries(monkeypatch):
    fake_entry = type(
        "FakeLogEntry",
        (),
        {
            "id": 99,
            "event_type": "ai_query_blocked",
            "severity": "high",
            "message": "Sensitive data detected in request",
            "created_at": datetime(2026, 3, 12, 10, 0, 0),
        },
    )()

    fake_session = FakeSession([FakeEntriesResult([fake_entry])])

    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get("/api/alerts/recent")

    assert response.status_code == 200
    data = response.json()

    assert "alerts" in data
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["id"] == "99"
    assert data["alerts"][0]["type"] == "ai_query_blocked"
    assert data["alerts"][0]["severity"] == "high"
    assert "Sensitive data detected in request" in data["alerts"][0]["message"]


def test_recent_alerts_endpoint_empty_fallback(monkeypatch):
    fake_session = FakeSession([FakeEntriesResult([])])

    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get("/api/alerts/recent")

    assert response.status_code == 200
    data = response.json()

    assert "alerts" in data
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["id"] == "0"
    assert data["alerts"][0]["type"] == "System"
    assert data["alerts"][0]["severity"] == "info"
    assert "No high-risk events logged yet" in data["alerts"][0]["message"]