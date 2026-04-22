"""
Reports API Router
------------------
Provides aggregated summary data for the Reports panel.

Aggregates LogEntry rows within a caller-supplied date range and
returns counts + breakdowns suitable for display and CSV export.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_

from app.auth.rbac import require_roles
from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.services.threat_detector import detect_threats
from app.utils.alert_manager import send_alert
from app.utils.db_encryption import is_encryption_enabled

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/summary")
async def get_reports_summary(
    start_date: Optional[str] = Query(
        default=None,
        description="ISO date string (YYYY-MM-DD). Defaults to 7 days ago.",
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="ISO date string (YYYY-MM-DD). Defaults to today (end of day).",
    ),
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Aggregated log statistics for the requested date range.

    Returns
    -------
    - total_requests
    - blocked / redacted / allowed counts
    - high / medium / low severity counts
    - breakdown by event_type  (top 10)
    - breakdown by policy_decision
    - top 5 endpoints by request volume
    - date range actually used
    """
    # Parse / default date bounds
    try:
        since = (
            datetime.strptime(start_date, "%Y-%m-%d")
            if start_date
            else datetime.utcnow() - timedelta(days=7)
        )
        until = (
            # include the full end day
            datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            if end_date
            else datetime.utcnow()
        )
    except ValueError:
        since = datetime.utcnow() - timedelta(days=7)
        until = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        base_filter = and_(LogEntry.created_at >= since, LogEntry.created_at <= until)

        # --- totals ---
        r_total = await session.execute(select(func.count()).where(base_filter))
        total = r_total.scalar() or 0

        r_blocked = await session.execute(
            select(func.count()).where(
                and_(base_filter, LogEntry.policy_decision == "block")
            )
        )
        blocked = r_blocked.scalar() or 0

        r_redacted = await session.execute(
            select(func.count()).where(
                and_(base_filter, LogEntry.policy_decision == "redact")
            )
        )
        redacted = r_redacted.scalar() or 0

        r_allowed = await session.execute(
            select(func.count()).where(
                and_(base_filter, LogEntry.policy_decision == "allow")
            )
        )
        allowed = r_allowed.scalar() or 0

        # --- severity breakdown ---
        r_high = await session.execute(
            select(func.count()).where(and_(base_filter, LogEntry.severity == "high"))
        )
        high = r_high.scalar() or 0

        r_medium = await session.execute(
            select(func.count()).where(and_(base_filter, LogEntry.severity == "medium"))
        )
        medium = r_medium.scalar() or 0

        r_low = await session.execute(
            select(func.count()).where(and_(base_filter, LogEntry.severity == "low"))
        )
        low = r_low.scalar() or 0

        # --- event_type breakdown (top 10) ---
        r_event_types = await session.execute(
            select(LogEntry.event_type, func.count().label("cnt"))
            .where(and_(base_filter, LogEntry.event_type.isnot(None)))
            .group_by(LogEntry.event_type)
            .order_by(func.count().desc())
            .limit(10)
        )
        event_type_breakdown = [
            {"event_type": row[0], "count": row[1]} for row in r_event_types.fetchall()
        ]

        # --- policy_decision breakdown ---
        r_decisions = await session.execute(
            select(LogEntry.policy_decision, func.count().label("cnt"))
            .where(and_(base_filter, LogEntry.policy_decision.isnot(None)))
            .group_by(LogEntry.policy_decision)
            .order_by(func.count().desc())
        )
        decision_breakdown = [
            {"decision": row[0], "count": row[1]} for row in r_decisions.fetchall()
        ]

        # --- top 5 endpoints ---
        r_endpoints = await session.execute(
            select(LogEntry.endpoint, func.count().label("cnt"))
            .where(base_filter)
            .group_by(LogEntry.endpoint)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_endpoints = [
            {"endpoint": row[0], "count": row[1]} for row in r_endpoints.fetchall()
        ]

    return {
        "period": {
            "start": since.strftime("%Y-%m-%d"),
            "end": until.strftime("%Y-%m-%d"),
        },
        "total_requests": total,
        "policy_decisions": {
            "blocked": blocked,
            "redacted": redacted,
            "allowed": allowed,
        },
        "severity": {
            "high": high,
            "medium": medium,
            "low": low,
        },
        "event_type_breakdown": event_type_breakdown,
        "decision_breakdown": decision_breakdown,
        "top_endpoints": top_endpoints,
    }


@router.get("/reports/remediation")
async def get_remediation_report(
    window_hours: int = Query(
        default=1, ge=1, le=24, description="Analysis window in hours (1–24)"
    ),
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    PSPR8 — Threat analysis + remediation report.

    Runs pattern detection across recent logs and returns:
    - Detected threat findings with severity
    - Step-by-step remediation actions per finding
    - An overall report status and summary

    Also fires Discord/Slack/email alerts for high-severity findings.
    """
    findings = await detect_threats(window_hours=window_hours)

    for finding in findings:
        if finding["severity"] == "high":
            send_alert(
                message=finding["description"],
                severity="high",
                source="threat_detector",
            )

    critical = [f for f in findings if f["severity"] == "high"]
    status = "THREATS_DETECTED" if findings else "CLEAN"
    overall_severity = "critical" if critical else ("medium" if findings else "none")

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "analysis_window_hours": window_hours,
        "status": status,
        "overall_severity": overall_severity,
        "total_findings": len(findings),
        "critical_findings": len(critical),
        "findings": findings,
        "summary": (
            f"{len(findings)} threat(s) detected ({len(critical)} critical). "
            "Review each finding and follow the remediation steps."
            if findings
            else "No threats detected in the analysis window. System operating normally."
        ),
    }


@router.get("/reports/db-audit")
async def get_db_audit(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    PSPR8 — Database security audit.

    Returns log volume, severity breakdown, 24h policy decision counts,
    high-risk event count, and database encryption status.
    """
    since_24h = datetime.utcnow() - timedelta(hours=24)

    async with AsyncSessionLocal() as session:
        total = (
            await session.execute(select(func.count()).select_from(LogEntry))
        ).scalar() or 0

        severity_breakdown: dict[str, int] = {}
        for level in ("low", "medium", "high"):
            severity_breakdown[level] = (
                await session.execute(
                    select(func.count()).where(LogEntry.severity == level)
                )
            ).scalar() or 0

        decision_breakdown: dict[str, int] = {}
        for decision in ("allow", "redact", "block"):
            decision_breakdown[decision] = (
                await session.execute(
                    select(func.count()).where(
                        and_(
                            LogEntry.policy_decision == decision,
                            LogEntry.created_at >= since_24h,
                        )
                    )
                )
            ).scalar() or 0

        high_risk_24h = (
            await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.risk_score >= 0.7,
                        LogEntry.created_at >= since_24h,
                    )
                )
            )
        ).scalar() or 0

    encryption_on = is_encryption_enabled()

    return {
        "audit_generated_at": datetime.utcnow().isoformat() + "Z",
        "total_log_entries": total,
        "severity_breakdown": severity_breakdown,
        "policy_decisions_24h": decision_breakdown,
        "high_risk_events_24h": high_risk_24h,
        "database_security": {
            "encryption_enabled": encryption_on,
            "encrypted_fields": ["logs.message"] if encryption_on else [],
            "audit_trail_active": True,
        },
    }
