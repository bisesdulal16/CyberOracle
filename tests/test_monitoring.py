"""
Tests for PSPR8 monitoring: threat_detector service and the
/api/reports/remediation + /api/reports/db-audit endpoints.

All DB calls are mocked so no running database is required.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
import app.routes.reports as reports_module
from app.services import threat_detector as td_module


# ── Auth helpers ──────────────────────────────────────────────────────────────


def _auth_headers(role: str = "admin") -> dict:
    token = create_access_token({"sub": role, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(reports_module.router)
    return TestClient(app)


# ── Fake DB session helpers ───────────────────────────────────────────────────


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, results):
        self._results = iter(results)

    async def execute(self, _query):
        return next(self._results)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


def _fake_session_ctx(results):
    return _FakeSession(results)


# ── threat_detector unit tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_threats_clean():
    """No threats when all queries return empty/zero."""
    session = _FakeSession(
        [
            _RowsResult([]),  # brute force
            _RowsResult([]),  # dlp bypass
            _ScalarResult(0),  # high-risk count
            _ScalarResult(0),  # total for spike check
            _ScalarResult(0),  # violations
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=1)
    assert findings == []


@pytest.mark.asyncio
async def test_detect_threats_brute_force():
    """BRUTE_FORCE finding when a source has >= threshold 401/403s."""

    class FakeRow:
        source = "10.0.0.1"
        cnt = 7

    session = _FakeSession(
        [
            _RowsResult([FakeRow()]),  # brute force rows
            _RowsResult([]),  # dlp bypass
            _ScalarResult(0),  # high-risk
            _ScalarResult(10),  # total
            _ScalarResult(2),  # violations (below spike ratio)
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=1)

    assert len(findings) == 1
    assert findings[0]["threat_type"] == "BRUTE_FORCE"
    assert findings[0]["severity"] == "high"
    assert findings[0]["source"] == "10.0.0.1"
    assert findings[0]["affected_count"] == 7
    assert len(findings[0]["remediation_steps"]) == 5


@pytest.mark.asyncio
async def test_detect_threats_dlp_bypass():
    """DLP_BYPASS_ATTEMPT finding when a source has >= threshold blocks."""

    class FakeRow:
        source = "attacker"
        cnt = 5

    session = _FakeSession(
        [
            _RowsResult([]),  # brute force
            _RowsResult([FakeRow()]),  # dlp bypass
            _ScalarResult(0),  # high-risk
            _ScalarResult(10),  # total
            _ScalarResult(2),  # violations
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=1)

    assert len(findings) == 1
    assert findings[0]["threat_type"] == "DLP_BYPASS_ATTEMPT"
    assert findings[0]["source"] == "attacker"


@pytest.mark.asyncio
async def test_detect_threats_high_risk_cluster():
    """HIGH_RISK_CLUSTER finding when high-risk count meets threshold."""
    session = _FakeSession(
        [
            _RowsResult([]),  # brute force
            _RowsResult([]),  # dlp bypass
            _ScalarResult(6),  # high-risk count (>= 5)
            _ScalarResult(10),  # total
            _ScalarResult(2),  # violations
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=1)

    assert len(findings) == 1
    assert findings[0]["threat_type"] == "HIGH_RISK_CLUSTER"
    assert findings[0]["severity"] == "high"
    assert findings[0]["affected_count"] == 6


@pytest.mark.asyncio
async def test_detect_threats_policy_spike():
    """POLICY_VIOLATION_SPIKE when > 50% requests are violations."""
    session = _FakeSession(
        [
            _RowsResult([]),  # brute force
            _RowsResult([]),  # dlp bypass
            _ScalarResult(0),  # high-risk
            _ScalarResult(10),  # total
            _ScalarResult(8),  # violations (80% > 50%)
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=1)

    assert len(findings) == 1
    assert findings[0]["threat_type"] == "POLICY_VIOLATION_SPIKE"
    assert findings[0]["severity"] == "medium"


@pytest.mark.asyncio
async def test_detect_threats_multiple():
    """Multiple threat types returned together."""

    class FakeBFRow:
        source = "bad-ip"
        cnt = 6

    class FakeDLPRow:
        source = "probe"
        cnt = 4

    session = _FakeSession(
        [
            _RowsResult([FakeBFRow()]),  # brute force
            _RowsResult([FakeDLPRow()]),  # dlp bypass
            _ScalarResult(7),  # high-risk cluster (>= 5)
            _ScalarResult(10),  # total
            _ScalarResult(9),  # violations spike
        ]
    )
    with patch.object(td_module, "AsyncSessionLocal", return_value=session):
        findings = await td_module.detect_threats(window_hours=6)

    types = {f["threat_type"] for f in findings}
    assert "BRUTE_FORCE" in types
    assert "DLP_BYPASS_ATTEMPT" in types
    assert "HIGH_RISK_CLUSTER" in types
    assert "POLICY_VIOLATION_SPIKE" in types


# ── /api/reports/remediation endpoint tests ───────────────────────────────────


def test_remediation_clean():
    """Returns CLEAN status when no threats detected."""
    client = _build_client()
    with patch.object(
        reports_module, "detect_threats", new_callable=AsyncMock
    ) as mock_dt:
        mock_dt.return_value = []
        resp = client.get(
            "/api/reports/remediation?window_hours=1", headers=_auth_headers()
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CLEAN"
    assert data["total_findings"] == 0
    assert data["findings"] == []


def test_remediation_threats_detected():
    """Returns THREATS_DETECTED with findings and fires alerts."""
    finding = {
        "threat_type": "BRUTE_FORCE",
        "severity": "high",
        "description": "Source x made 7 failed attempts in 1h",
        "affected_count": 7,
        "source": "x",
        "recommendation": "Block source.",
        "remediation_steps": ["Step 1", "Step 2"],
    }
    client = _build_client()
    with patch.object(
        reports_module, "detect_threats", new_callable=AsyncMock
    ) as mock_dt, patch("app.routes.reports.send_alert") as mock_alert:
        mock_dt.return_value = [finding]
        resp = client.get(
            "/api/reports/remediation?window_hours=1", headers=_auth_headers()
        )
        mock_alert.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "THREATS_DETECTED"
    assert data["overall_severity"] == "critical"
    assert data["total_findings"] == 1
    assert data["critical_findings"] == 1
    assert data["findings"][0]["threat_type"] == "BRUTE_FORCE"


def test_remediation_medium_only():
    """overall_severity is 'medium' when only medium findings present."""
    finding = {
        "threat_type": "POLICY_VIOLATION_SPIKE",
        "severity": "medium",
        "description": "Spike",
        "affected_count": 5,
        "source": "system-wide",
        "recommendation": "Review.",
        "remediation_steps": [],
    }
    client = _build_client()
    with patch.object(
        reports_module, "detect_threats", new_callable=AsyncMock
    ) as mock_dt:
        mock_dt.return_value = [finding]
        resp = client.get(
            "/api/reports/remediation?window_hours=1", headers=_auth_headers()
        )
    assert resp.status_code == 200
    assert resp.json()["overall_severity"] == "medium"


def test_remediation_requires_auth():
    """Returns 403 with no Authorization header (no token = 403 from RBAC)."""
    client = _build_client()
    resp = client.get("/api/reports/remediation")
    assert resp.status_code in (401, 403)


# ── /api/reports/db-audit endpoint tests ─────────────────────────────────────


def test_db_audit_returns_200():
    """DB audit endpoint returns 200 with expected keys."""
    client = _build_client()

    fake_results = [
        _ScalarResult(50),  # total
        _ScalarResult(10),  # low severity
        _ScalarResult(5),  # medium severity
        _ScalarResult(15),  # high severity
        _ScalarResult(3),  # allow 24h
        _ScalarResult(2),  # redact 24h
        _ScalarResult(1),  # block 24h
        _ScalarResult(4),  # high_risk 24h
    ]

    with patch.object(
        reports_module,
        "AsyncSessionLocal",
        return_value=_fake_session_ctx(fake_results),
    ), patch("app.routes.reports.is_encryption_enabled", return_value=True):
        resp = client.get("/api/reports/db-audit", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_log_entries"] == 50
    assert data["severity_breakdown"] == {"low": 10, "medium": 5, "high": 15}
    assert data["policy_decisions_24h"] == {"allow": 3, "redact": 2, "block": 1}
    assert data["high_risk_events_24h"] == 4
    assert data["database_security"]["encryption_enabled"] is True
    assert "logs.message" in data["database_security"]["encrypted_fields"]
    assert data["database_security"]["audit_trail_active"] is True


def test_db_audit_encryption_disabled():
    """DB audit reflects encryption_enabled=False and empty encrypted_fields."""
    client = _build_client()

    fake_results = [
        _ScalarResult(0),  # total
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
        _ScalarResult(0),
    ]

    with patch.object(
        reports_module,
        "AsyncSessionLocal",
        return_value=_fake_session_ctx(fake_results),
    ), patch("app.routes.reports.is_encryption_enabled", return_value=False):
        resp = client.get("/api/reports/db-audit", headers=_auth_headers())

    assert resp.status_code == 200
    data = resp.json()
    assert data["database_security"]["encryption_enabled"] is False
    assert data["database_security"]["encrypted_fields"] == []


def test_db_audit_requires_auth():
    """Returns 401/403 without a valid token."""
    client = _build_client()
    resp = client.get("/api/reports/db-audit")
    assert resp.status_code in (401, 403)
