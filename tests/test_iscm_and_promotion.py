"""
Tests for DoD DevSecOps Monitor Phase additions:
  - GET /api/iscm/status
  - POST /api/logs/promote
  - app.services.log_promoter.promote_logs
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
import app.routes.metrics as metrics_module
import app.services.log_promoter as promoter_module


# ── Auth helpers ──────────────────────────────────────────────────────────────


def _auth_headers(role: str = "admin") -> dict:
    token = create_access_token({"sub": role, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ── Fake DB session helpers (shared pattern from other test files) ─────────────


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _ScalarsResult:
    def __init__(self, entries):
        self._entries = entries

    def scalars(self):
        return self

    def all(self):
        return self._entries


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self._index = 0

    async def execute(self, _query):
        result = self._results[self._index]
        self._index += 1
        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


def _session_ctx(results):
    return _FakeSession(results)


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(metrics_module.router)
    return TestClient(app)


# ── /api/iscm/status tests ────────────────────────────────────────────────────


def test_iscm_status_returns_200(monkeypatch):
    """ISCM status endpoint returns 200 with all expected top-level keys."""
    fake_results = [
        _ScalarResult(100),  # total_all
        _ScalarResult(80),   # total_allowed
        _ScalarResult(0),    # high_risk_1h
        _ScalarResult(0),    # blocked_1h
        _ScalarResult(90),   # total_with_hash
        _ScalarResult(10),   # total_24h
        _ScalarResult(2),    # promotions_24h
    ]
    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: _session_ctx(fake_results),
    )
    client = _build_client()
    resp = client.get("/api/iscm/status", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert "assessed_at" in data
    assert "monitoring_health" in data
    assert "compliance" in data
    assert "threat_indicators" in data
    assert "log_integrity" in data
    assert "activity_24h" in data
    assert "data_protection" in data
    assert "alert_channels" in data


def test_iscm_status_healthy(monkeypatch):
    """Reports 'healthy' when compliance is high and no threats."""
    fake_results = [
        _ScalarResult(100),  # total
        _ScalarResult(95),   # allowed (95% = high compliance)
        _ScalarResult(0),    # high_risk_1h
        _ScalarResult(0),    # blocked_1h
        _ScalarResult(100),  # integrity_hashed
        _ScalarResult(50),   # 24h requests
        _ScalarResult(1),    # promotions
    ]
    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: _session_ctx(fake_results),
    )
    client = _build_client()
    resp = client.get("/api/iscm/status", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["monitoring_health"] == "healthy"
    assert data["threat_indicators"]["level"] == "none"
    assert data["compliance"]["score"] == pytest.approx(0.95, rel=1e-3)


def test_iscm_status_degraded_on_high_threats(monkeypatch):
    """Reports 'degraded' when high-risk events exceed threshold."""
    fake_results = [
        _ScalarResult(100),
        _ScalarResult(30),   # low compliance
        _ScalarResult(15),   # high_risk_1h >= 10 → threat level high
        _ScalarResult(1),
        _ScalarResult(50),
        _ScalarResult(20),
        _ScalarResult(0),
    ]
    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: _session_ctx(fake_results),
    )
    client = _build_client()
    resp = client.get("/api/iscm/status", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["monitoring_health"] == "degraded"
    assert data["threat_indicators"]["level"] == "high"


def test_iscm_status_warning_medium_threats(monkeypatch):
    """Reports 'warning' when threat level is medium."""
    fake_results = [
        _ScalarResult(100),
        _ScalarResult(82),   # 82% compliance (>= 0.8)
        _ScalarResult(4),    # high_risk_1h in [3,9] → medium
        _ScalarResult(1),
        _ScalarResult(80),
        _ScalarResult(10),
        _ScalarResult(0),
    ]
    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: _session_ctx(fake_results),
    )
    client = _build_client()
    resp = client.get("/api/iscm/status", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["monitoring_health"] == "warning"
    assert data["threat_indicators"]["level"] == "medium"


def test_iscm_status_no_data(monkeypatch):
    """Returns healthy defaults when the database has no entries yet."""
    fake_results = [
        _ScalarResult(0),  # total_all
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
    ]
    monkeypatch.setattr(
        metrics_module,
        "AsyncSessionLocal",
        lambda: _session_ctx(fake_results),
    )
    client = _build_client()
    resp = client.get("/api/iscm/status", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["compliance"]["score"] == 0.0
    assert data["log_integrity"]["coverage"] == 1.0  # 0/0 → 1.0 (full coverage vacuously)
    assert data["threat_indicators"]["level"] == "none"


def test_iscm_status_requires_auth():
    """Returns 401/403 without a valid token."""
    client = _build_client()
    resp = client.get("/api/iscm/status")
    assert resp.status_code in (401, 403)


# ── /api/logs/promote endpoint tests ─────────────────────────────────────────


def test_promote_logs_endpoint_no_entries():
    """Returns 200 with promoted_count=0 when no high-risk entries exist."""
    client = _build_client()
    with patch("app.services.log_promoter.promote_logs", new_callable=AsyncMock) as mock_promote:
        mock_promote.return_value = []
        resp = client.post("/api/logs/promote?window_hours=24", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["promoted_count"] == 0
    assert data["promoted_entries"] == []
    assert data["window_hours"] == 24
    assert "promoted_at" in data


def test_promote_logs_endpoint_with_entries():
    """Returns promoted entries when high-risk logs exist."""
    fake_entry = {
        "id": 42,
        "event_type": "ai_query_blocked",
        "severity": "high",
        "risk_score": 0.85,
        "source": "attacker",
        "endpoint": "/ai/query",
        "created_at": "2026-04-01T12:00:00Z",
    }
    client = _build_client()
    with patch("app.services.log_promoter.promote_logs", new_callable=AsyncMock) as mock_promote:
        mock_promote.return_value = [fake_entry]
        resp = client.post("/api/logs/promote?window_hours=12", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["promoted_count"] == 1
    assert data["window_hours"] == 12
    assert data["promoted_entries"][0]["id"] == 42
    assert data["promoted_entries"][0]["risk_score"] == pytest.approx(0.85)


def test_promote_logs_endpoint_requires_auth():
    """Returns 401/403 without a valid token."""
    client = _build_client()
    resp = client.post("/api/logs/promote")
    assert resp.status_code in (401, 403)


def test_promote_logs_endpoint_invalid_window():
    """Rejects window_hours outside the allowed range."""
    client = _build_client()
    resp = client.post("/api/logs/promote?window_hours=999", headers=_auth_headers())
    assert resp.status_code == 422


# ── log_promoter service unit tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_promote_logs_empty_db():
    """Returns empty list when no high-risk entries exist."""
    session = _FakeSession([_ScalarsResult([])])
    with patch.object(promoter_module, "AsyncSessionLocal", return_value=session):
        result = await promoter_module.promote_logs(window_hours=24)
    assert result == []


@pytest.mark.asyncio
async def test_promote_logs_sends_alerts_and_audit():
    """Fires send_alert and log_request for each promoted entry."""
    from datetime import datetime

    class FakeEntry:
        id = 7
        event_type = "ai_query_blocked"
        severity = "high"
        risk_score = 0.9
        source = "test-source"
        endpoint = "/ai/query"
        created_at = datetime(2026, 1, 1, 12, 0, 0)

    session = _FakeSession([_ScalarsResult([FakeEntry()])])

    with patch.object(promoter_module, "AsyncSessionLocal", return_value=session), \
         patch.object(promoter_module, "send_alert") as mock_alert, \
         patch.object(promoter_module, "log_request", new_callable=AsyncMock) as mock_log:
        result = await promoter_module.promote_logs(window_hours=24)

    assert len(result) == 1
    assert result[0]["id"] == 7
    assert result[0]["risk_score"] == pytest.approx(0.9)
    mock_alert.assert_called_once()
    mock_log.assert_called_once()
    call_kwargs = mock_log.call_args.kwargs
    assert call_kwargs["event_type"] == "log_promoted"
    assert "7" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_promote_logs_deduplicates_entries():
    """Each entry ID is only promoted once even if returned multiple times."""
    from datetime import datetime

    class FakeEntry:
        id = 5
        event_type = "dlp_alert"
        severity = "high"
        risk_score = 0.8
        source = "probe"
        endpoint = "/ai/query"
        created_at = datetime(2026, 1, 1, 10, 0, 0)

    session = _FakeSession([_ScalarsResult([FakeEntry(), FakeEntry()])])

    with patch.object(promoter_module, "AsyncSessionLocal", return_value=session), \
         patch.object(promoter_module, "send_alert") as mock_alert, \
         patch.object(promoter_module, "log_request", new_callable=AsyncMock):
        result = await promoter_module.promote_logs(window_hours=24)

    assert len(result) == 1
    mock_alert.assert_called_once()
