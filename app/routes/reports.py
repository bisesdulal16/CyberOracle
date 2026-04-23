"""
Reports API Router
------------------
Provides aggregated summary data for the Reports panel.

Aggregates LogEntry rows within a caller-supplied date range and
returns counts + breakdowns suitable for display and CSV export.

Input validation applied to date parameters to prevent injection.
OWASP API3: Broken Object Property Level Authorization
"""

import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_

from app.auth.rbac import require_roles
from app.db.db import AsyncSessionLocal
from app.models import LogEntry

router = APIRouter(prefix="/api", tags=["reports"])

# Strict date format: YYYY-MM-DD only
# OWASP API3: Prevents injection via malformed date parameters
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(date_str: Optional[str], default: datetime) -> datetime:
    """
    Parse and validate a date string in YYYY-MM-DD format.
    Returns default if input is None, empty, or malformed.
    Strict regex check applied before strptime to prevent injection.
    """
    if not date_str:
        return default
    if not DATE_PATTERN.match(date_str):
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return default


@router.get("/reports/summary")
async def get_reports_summary(
    start_date: Optional[str] = Query(
        default=None,
        description="ISO date string (YYYY-MM-DD). Defaults to 7 days ago.",
        max_length=10,
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="ISO date string (YYYY-MM-DD). Defaults to today.",
        max_length=10,
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
    - breakdown by event_type (top 10)
    - breakdown by policy_decision
    - top 5 endpoints by request volume
    - date range actually used
    """
    since = _parse_date(start_date, datetime.utcnow() - timedelta(days=7))
    until = _parse_date(end_date, datetime.utcnow())

    # Include the full end day
    if end_date and DATE_PATTERN.match(end_date):
        until = until.replace(hour=23, minute=59, second=59)

    async with AsyncSessionLocal() as session:
        base_filter = and_(LogEntry.created_at >= since, LogEntry.created_at <= until)

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

        r_decisions = await session.execute(
            select(LogEntry.policy_decision, func.count().label("cnt"))
            .where(and_(base_filter, LogEntry.policy_decision.isnot(None)))
            .group_by(LogEntry.policy_decision)
            .order_by(func.count().desc())
        )
        decision_breakdown = [
            {"decision": row[0], "count": row[1]} for row in r_decisions.fetchall()
        ]

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
