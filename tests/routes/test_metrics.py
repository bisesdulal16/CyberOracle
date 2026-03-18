from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
from app.main import app
import app.routes.metrics as metrics_module


def _auth_headers(username="admin", role="admin"):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


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


def test_metrics_summary_authorized(monkeypatch):
    fake_session = FakeSession(
        [
            FakeScalarResult(12),  # total_prompts_24h
            FakeScalarResult(3),  # blocked_prompts
            FakeScalarResult(2),  # redacted_outputs
            FakeScalarResult(1),  # high_risk_events
        ]
    )

    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    response = client.get(
        "/api/metrics/summary",
        headers=_auth_headers(),
    )
    assert response.status_code == 200

    data = response.json()
    assert data["total_prompts_24h"] == 12
    assert data["blocked_prompts"] == 3
    assert data["redacted_outputs"] == 2
    assert data["high_risk_events"] == 1
    assert data["active_models"] == 1


def test_compliance_status_authorized():
    response = client.get(
        "/api/compliance/status",
        headers=_auth_headers(),
    )
    assert response.status_code == 200

    data = response.json()
    assert "compliance_score" in data
    assert "compliant_controls" in data
    assert "non_compliant_controls" in data
    assert "total_controls" in data
    assert "frameworks" in data

    frameworks = data["frameworks"]
    assert "HIPAA" in frameworks
    assert "FERPA" in frameworks
    assert "NIST_CSF" in frameworks
    assert "GDPR" in frameworks


def test_metrics_summary_requires_auth():
    response = client.get("/api/metrics/summary")
    assert response.status_code in (401, 403)


def test_compliance_status_requires_auth():
    response = client.get("/api/compliance/status")
    assert response.status_code in (401, 403)


def test_alerts_recent_requires_auth():
    response = client.get("/api/alerts/recent")
    assert response.status_code in (401, 403)
