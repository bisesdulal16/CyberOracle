"""
Threat Detector Service (PSPR8)
--------------------------------
Queries the log database and detects malicious activity patterns.
Also provides remediation step mappings for each threat type.

Threat patterns detected:
- BRUTE_FORCE            : High rate of 401/403 responses from the same source
- DLP_BYPASS_ATTEMPT     : Repeated 'block' decisions from the same source
- HIGH_RISK_CLUSTER      : Multiple high-risk events (risk_score >= 0.7) in window
- POLICY_VIOLATION_SPIKE : > 50% of requests triggered block/redact decisions
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select

from app.db.db import AsyncSessionLocal
from app.models import LogEntry

BRUTE_FORCE_THRESHOLD = 5
DLP_BYPASS_THRESHOLD = 3
HIGH_RISK_CLUSTER_THRESHOLD = 5
POLICY_SPIKE_RATIO = 0.5

REMEDIATION_STEPS: dict[str, list[str]] = {
    "BRUTE_FORCE": [
        "Block the offending source IP at the firewall or API gateway.",
        "Enforce account lockout after 5 consecutive failed attempts.",
        "Enable multi-factor authentication (MFA) for all API consumers.",
        "Tighten rate limits on /auth endpoints.",
        "Audit accounts for any successful unauthorized access.",
    ],
    "DLP_BYPASS_ATTEMPT": [
        "Review blocked payloads for the flagged source in the audit log.",
        "Revoke or rotate API credentials for the offending source.",
        "Lower DLP risk score thresholds if probe patterns are confirmed.",
        "Initiate a formal incident response procedure.",
        "Verify no data was exfiltrated before detection.",
    ],
    "HIGH_RISK_CLUSTER": [
        "Identify all sources contributing to high-risk events.",
        "Correlate high-risk log entries for common attack patterns.",
        "Escalate to the security team for manual investigation.",
        "Temporarily restrict access to high-risk endpoints.",
        "Update threat detection rules to catch emerging patterns.",
    ],
    "POLICY_VIOLATION_SPIKE": [
        "Audit recent policy changes that may have tightened rules inadvertently.",
        "Review client configurations sending non-compliant data.",
        "Investigate whether the spike indicates an ongoing attack campaign.",
        "Generate a full compliance report for the affected time window.",
        "Notify stakeholders about the elevated violation rate.",
    ],
}


async def detect_threats(window_hours: int = 1) -> list[dict[str, Any]]:
    """
    Run threat detection across logs from the past `window_hours`.

    Returns a list of findings. Each finding includes:
      threat_type       — machine-readable category
      severity          — "high" | "medium"
      description       — human-readable summary
      affected_count    — number of events triggering this finding
      source            — originating source label
      recommendation    — one-line remediation hint
      remediation_steps — ordered list of remediation actions
    """
    since = datetime.utcnow() - timedelta(hours=window_hours)
    findings: list[dict[str, Any]] = []

    async with AsyncSessionLocal() as session:

        # ── Brute Force: high rate of 401/403 from same source ────────────
        auth_fail_rows = (
            await session.execute(
                select(LogEntry.source, func.count().label("cnt"))
                .where(
                    and_(
                        LogEntry.status_code.in_([401, 403]),
                        LogEntry.created_at >= since,
                    )
                )
                .group_by(LogEntry.source)
                .having(func.count() >= BRUTE_FORCE_THRESHOLD)
            )
        ).all()

        for row in auth_fail_rows:
            findings.append(
                {
                    "threat_type": "BRUTE_FORCE",
                    "severity": "high",
                    "description": (
                        f"Source '{row.source}' made {row.cnt} failed authentication "
                        f"attempts in {window_hours}h"
                    ),
                    "affected_count": row.cnt,
                    "source": row.source,
                    "recommendation": "Block source, enforce MFA, tighten rate limits on /auth.",
                    "remediation_steps": REMEDIATION_STEPS["BRUTE_FORCE"],
                }
            )

        # ── DLP Bypass Probes: repeated blocks from same source ───────────
        block_rows = (
            await session.execute(
                select(LogEntry.source, func.count().label("cnt"))
                .where(
                    and_(
                        LogEntry.policy_decision == "block",
                        LogEntry.created_at >= since,
                    )
                )
                .group_by(LogEntry.source)
                .having(func.count() >= DLP_BYPASS_THRESHOLD)
            )
        ).all()

        for row in block_rows:
            findings.append(
                {
                    "threat_type": "DLP_BYPASS_ATTEMPT",
                    "severity": "high",
                    "description": (
                        f"Source '{row.source}' triggered {row.cnt} DLP blocks in "
                        f"{window_hours}h — possible data exfiltration probe"
                    ),
                    "affected_count": row.cnt,
                    "source": row.source,
                    "recommendation": "Revoke credentials, review payloads, tighten DLP policies.",
                    "remediation_steps": REMEDIATION_STEPS["DLP_BYPASS_ATTEMPT"],
                }
            )

        # ── High-Risk Cluster: many high-risk events system-wide ──────────
        high_count = (
            await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.risk_score >= 0.7,
                        LogEntry.created_at >= since,
                    )
                )
            )
        ).scalar() or 0

        if high_count >= HIGH_RISK_CLUSTER_THRESHOLD:
            findings.append(
                {
                    "threat_type": "HIGH_RISK_CLUSTER",
                    "severity": "high",
                    "description": (
                        f"{high_count} high-risk events (risk_score ≥ 0.7) detected "
                        f"in {window_hours}h"
                    ),
                    "affected_count": high_count,
                    "source": "multiple",
                    "recommendation": (
                        "Investigate sources, restrict endpoints, escalate to security team."
                    ),
                    "remediation_steps": REMEDIATION_STEPS["HIGH_RISK_CLUSTER"],
                }
            )

        # ── Policy Violation Spike: > 50% of requests are violations ──────
        total = (
            await session.execute(
                select(func.count()).where(LogEntry.created_at >= since)
            )
        ).scalar() or 0

        violations = (
            await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.policy_decision.in_(["block", "redact"]),
                        LogEntry.created_at >= since,
                    )
                )
            )
        ).scalar() or 0

        if total > 0 and (violations / total) > POLICY_SPIKE_RATIO:
            pct = round(violations / total * 100)
            findings.append(
                {
                    "threat_type": "POLICY_VIOLATION_SPIKE",
                    "severity": "medium",
                    "description": (
                        f"{violations}/{total} requests ({pct}%) triggered policy "
                        f"violations in {window_hours}h"
                    ),
                    "affected_count": violations,
                    "source": "system-wide",
                    "recommendation": (
                        "Review policies, investigate clients, check for active attack."
                    ),
                    "remediation_steps": REMEDIATION_STEPS["POLICY_VIOLATION_SPIKE"],
                }
            )

    return findings
