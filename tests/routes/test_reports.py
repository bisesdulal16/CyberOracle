from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
import app.routes.reports as reports_module


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class FakeRowsResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


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


def _auth_headers(username="admin", role="admin"):
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


def build_client():
    app = FastAPI()
    app.include_router(reports_module.router)
    return TestClient(app)


def test_reports_summary_defaults(monkeypatch):
    fake_session = FakeSession(
        [
            FakeScalarResult(20),
            FakeScalarResult(5),
            FakeScalarResult(7),
            FakeScalarResult(8),
            FakeScalarResult(3),
            FakeScalarResult(9),
            FakeScalarResult(8),
            FakeRowsResult([("ai_query", 10), ("document_sanitize", 4)]),
            FakeRowsResult([("allow", 8), ("redact", 7), ("block", 5)]),
            FakeRowsResult([("/ai/query", 12), ("/api/documents/sanitize", 8)]),
        ]
    )

    monkeypatch.setattr(
        reports_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get("/api/reports/summary", headers=_auth_headers())

    assert response.status_code == 200
    data = response.json()

    assert "period" in data
    assert data["total_requests"] == 20
    assert data["policy_decisions"]["blocked"] == 5
    assert data["policy_decisions"]["redacted"] == 7
    assert data["policy_decisions"]["allowed"] == 8
    assert data["severity"]["high"] == 3
    assert data["severity"]["medium"] == 9
    assert data["severity"]["low"] == 8
    assert data["event_type_breakdown"] == [
        {"event_type": "ai_query", "count": 10},
        {"event_type": "document_sanitize", "count": 4},
    ]
    assert data["decision_breakdown"] == [
        {"decision": "allow", "count": 8},
        {"decision": "redact", "count": 7},
        {"decision": "block", "count": 5},
    ]
    assert data["top_endpoints"] == [
        {"endpoint": "/ai/query", "count": 12},
        {"endpoint": "/api/documents/sanitize", "count": 8},
    ]


def test_reports_summary_with_explicit_dates(monkeypatch):
    fake_session = FakeSession(
        [
            FakeScalarResult(1),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(1),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(1),
            FakeRowsResult([]),
            FakeRowsResult([]),
            FakeRowsResult([]),
        ]
    )

    monkeypatch.setattr(
        reports_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get(
        "/api/reports/summary?start_date=2026-03-01&end_date=2026-03-07",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["period"]["start"] == "2026-03-01"
    assert data["period"]["end"] == "2026-03-07"
    assert data["total_requests"] == 1


def test_reports_summary_invalid_dates_fall_back(monkeypatch):
    fake_session = FakeSession(
        [
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeScalarResult(0),
            FakeRowsResult([]),
            FakeRowsResult([]),
            FakeRowsResult([]),
        ]
    )

    monkeypatch.setattr(
        reports_module,
        "AsyncSessionLocal",
        lambda: FakeSessionContext(fake_session),
    )

    client = build_client()
    response = client.get(
        "/api/reports/summary?start_date=bad-date&end_date=also-bad",
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "start" in data["period"]
    assert "end" in data["period"]


def test_reports_summary_requires_auth():
    client = build_client()
    response = client.get("/api/reports/summary")
    assert response.status_code in (401, 403)
