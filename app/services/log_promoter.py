"""
Log Promotion Service  (DoD DevSecOps Monitor Phase)
------------------------------------------------------
Identifies high-severity log entries and promotes them to external
monitoring channels, satisfying the DoD DevSecOps Fundamentals
Guidebook requirement for "Log promotion" in the Monitor phase.

Log promotion escalates significant security events from the
application log store to external SIEM channels (Discord/Slack/email)
and creates an audit trail entry confirming promotion occurred.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select

from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.utils.alert_manager import send_alert
from app.utils.logger import log_request

PROMOTION_RISK_THRESHOLD = 0.7
PROMOTION_WINDOW_HOURS = 24


async def promote_logs(
    window_hours: int = PROMOTION_WINDOW_HOURS,
) -> list[dict[str, Any]]:
    """
    Query high-risk log entries from the past window and promote them.

    Promotion consists of:
    1. Sending an alert via configured channels (Discord / Slack / email)
       for each entry above the risk threshold.
    2. Writing a single 'log_promoted' audit entry recording the
       promoted IDs so that promotion is traceable.

    Returns the list of promoted entry summaries (id + metadata).
    """
    since = datetime.utcnow() - timedelta(hours=window_hours)
    promoted: list[dict[str, Any]] = []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(LogEntry)
            .where(
                and_(
                    LogEntry.created_at >= since,
                    LogEntry.risk_score >= PROMOTION_RISK_THRESHOLD,
                    LogEntry.severity == "high",
                )
            )
            .order_by(LogEntry.created_at.desc())
            .limit(50)
        )
        entries = result.scalars().all()

    seen_ids: set[int] = set()
    for entry in entries:
        if entry.id in seen_ids:
            continue
        seen_ids.add(entry.id)

        summary: dict[str, Any] = {
            "id": entry.id,
            "event_type": entry.event_type,
            "severity": entry.severity,
            "risk_score": entry.risk_score,
            "source": entry.source,
            "endpoint": entry.endpoint,
            "created_at": (
                entry.created_at.isoformat() + "Z" if entry.created_at else None
            ),
        }
        promoted.append(summary)

        send_alert(
            message=(
                f"[Log Promotion] Entry #{entry.id} escalated — "
                f"event_type={entry.event_type}, risk_score={entry.risk_score:.2f}, "
                f"source={entry.source}, endpoint={entry.endpoint}"
            ),
            severity=entry.severity or "high",
            source="log_promoter",
        )

    # Write a single promotion audit record covering all promoted IDs
    if promoted:
        ids_str = ", ".join(str(e["id"]) for e in promoted)
        await log_request(
            endpoint="/api/logs/promote",
            method="POST",
            status_code=200,
            message=f"Promoted {len(promoted)} high-risk log entries: [{ids_str}]",
            event_type="log_promoted",
            severity="info",
            source="log_promoter",
            policy_decision="allow",
        )

    return promoted
