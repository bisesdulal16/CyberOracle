"""
Reports API Router
------------------
Provides aggregated summary data for the Reports panel.

Aggregates LogEntry rows within a caller-supplied date range and
returns counts + breakdowns suitable for display and CSV export.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_

from app.db.db import AsyncSessionLocal
from app.models import LogEntry

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
        base_filter = and_(
            LogEntry.created_at >= since, LogEntry.created_at <= until
        )

        # --- totals ---
        r_total = await session.execute(
            select(func.count()).where(base_filter)
        )
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
            select(func.count()).where(
                and_(base_filter, LogEntry.severity == "high")
            )
        )
        high = r_high.scalar() or 0

        r_medium = await session.execute(
            select(func.count()).where(
                and_(base_filter, LogEntry.severity == "medium")
            )
        )
        medium = r_medium.scalar() or 0

        r_low = await session.execute(
            select(func.count()).where(
                and_(base_filter, LogEntry.severity == "low")
            )
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
            {"event_type": row[0], "count": row[1]}
            for row in r_event_types.fetchall()
        ]

        # --- policy_decision breakdown ---
        r_decisions = await session.execute(
            select(LogEntry.policy_decision, func.count().label("cnt"))
            .where(and_(base_filter, LogEntry.policy_decision.isnot(None)))
            .group_by(LogEntry.policy_decision)
            .order_by(func.count().desc())
        )
        decision_breakdown = [
            {"decision": row[0], "count": row[1]}
            for row in r_decisions.fetchall()
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
            {"endpoint": row[0], "count": row[1]}
            for row in r_endpoints.fetchall()
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
