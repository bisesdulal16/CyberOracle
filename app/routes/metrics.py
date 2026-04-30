# app/routes/metrics.py

import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.auth.rbac import require_roles
from app.auth.policy_loader import load_policy
from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.utils.db_encryption import is_encryption_enabled, get_key_id, decrypt_value

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics/summary")
async def get_metrics_summary(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Real-time dashboard metrics sourced from the logs table.
    Counts are scoped to the past 24 hours.
    """
    since = datetime.utcnow() - timedelta(hours=24)

    async with AsyncSessionLocal() as session:
        # Total requests in the past 24h — Secure Chat + Document Sanitizer
        r_total = await session.execute(
            select(func.count()).where(
                and_(
                    LogEntry.endpoint.in_(["/ai/query", "/api/documents/sanitize"]),
                    LogEntry.created_at >= since,
                )
            )
        )
        total_prompts = r_total.scalar() or 0

        # DLP blocked — policy_decision='block' from any source
        r_blocked = await session.execute(
            select(func.count()).where(
                and_(
                    LogEntry.policy_decision == "block",
                    LogEntry.created_at >= since,
                )
            )
        )
        blocked = r_blocked.scalar() or 0

        # Redacted outputs
        r_redacted = await session.execute(
            select(func.count()).where(
                and_(
                    LogEntry.policy_decision == "redact",
                    LogEntry.created_at >= since,
                )
            )
        )
        redacted = r_redacted.scalar() or 0

        # High-risk events (risk_score >= 0.7)
        r_high = await session.execute(
            select(func.count()).where(
                and_(LogEntry.risk_score >= 0.7, LogEntry.created_at >= since)
            )
        )
        high_risk = r_high.scalar() or 0

    return {
        "total_prompts_24h": total_prompts,
        "blocked_prompts": blocked,
        "redacted_outputs": redacted,
        "high_risk_events": high_risk,
        "active_models": 1,  # Ollama only for Capstone I MVP
    }


@router.get("/compliance/status")
async def get_compliance_status(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Compliance scores computed from real activity in the logs table.

    Two data sources:
      - Secure Chat  (/ai/query)              → HIPAA framework
      - Document Sanitizer (/api/documents/sanitize) → FERPA framework
      - Combined overall                      → NIST CSF + GDPR

    A "compliant" interaction is one where policy_decision = 'allow'
    (no PII/sensitive data detected).  'block' or 'redact' = non-compliant.
    """

    def _status(score: float) -> str:
        if score >= 0.9:
            return "compliant"
        if score >= 0.5:
            return "partial"
        return "non_compliant"

    def _safe_score(allowed: int, total: int) -> float:
        # 0/0 → 0.0 (no data yet, not vacuously "100% compliant")
        return round(allowed / total, 4) if total > 0 else 0.0

    chat_total = chat_allowed = doc_total = doc_allowed = 0
    try:
        async with AsyncSessionLocal() as session:
            # ── Secure Chat (/ai/query) ────────────────────────────────────
            r_chat_total = await session.execute(
                select(func.count()).where(LogEntry.endpoint == "/ai/query")
            )
            chat_total = r_chat_total.scalar() or 0

            r_chat_allowed = await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.endpoint == "/ai/query",
                        LogEntry.policy_decision == "allow",
                    )
                )
            )
            chat_allowed = r_chat_allowed.scalar() or 0

            # ── Document Sanitizer (/api/documents/sanitize) ───────────────
            r_doc_total = await session.execute(
                select(func.count()).where(
                    LogEntry.endpoint == "/api/documents/sanitize"
                )
            )
            doc_total = r_doc_total.scalar() or 0

            r_doc_allowed = await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.endpoint == "/api/documents/sanitize",
                        LogEntry.policy_decision == "allow",
                    )
                )
            )
            doc_allowed = r_doc_allowed.scalar() or 0
    except Exception:
        # DB unavailable (e.g. CI environment without a running database).
        # Return zero counts so the endpoint still responds 200.
        pass

    # ── Aggregates ─────────────────────────────────────────────────────────
    total = chat_total + doc_total
    compliant = chat_allowed + doc_allowed
    non_compliant = total - compliant
    overall_score = _safe_score(compliant, total)

    hipaa_score = _safe_score(chat_allowed, chat_total)
    ferpa_score = _safe_score(doc_allowed, doc_total)

    return {
        "compliance_score": overall_score,
        "compliant_controls": compliant,
        "non_compliant_controls": non_compliant,
        "total_controls": total,
        "frameworks": {
            "HIPAA": {
                "score": hipaa_score,
                "status": _status(hipaa_score),
                "compliant": chat_allowed,
                "total": chat_total,
            },
            "FERPA": {
                "score": ferpa_score,
                "status": _status(ferpa_score),
                "compliant": doc_allowed,
                "total": doc_total,
            },
            "NIST_CSF": {
                "score": overall_score,
                "status": _status(overall_score),
                "compliant": compliant,
                "total": total,
            },
            "GDPR": {
                "score": overall_score,
                "status": _status(overall_score),
                "compliant": compliant,
                "total": total,
            },
        },
    }


@router.get("/alerts/recent")
async def get_recent_alerts(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Recent high-severity events from the logs table.
    Falls back to a placeholder if no events exist yet.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(LogEntry)
            .where(LogEntry.severity == "high")
            .order_by(LogEntry.created_at.desc())
            .limit(10)
        )
        entries = result.scalars().all()

    alerts = [
        {
            "id": str(entry.id),
            "type": entry.event_type or "Security Event",
            "severity": entry.severity or "high",
            "message": (decrypt_value(entry.message) or "")[:200],
            "timestamp": entry.created_at.isoformat() + "Z" if entry.created_at else "",
        }
        for entry in entries
    ]

    # If the DB is empty (e.g. fresh install), return a clear placeholder
    if not alerts:
        alerts = [
            {
                "id": "0",
                "type": "System",
                "severity": "info",
                "message": (
                    "No high-risk events logged yet. "
                    "Alerts will appear here after activity."
                ),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        ]

    return {"alerts": alerts}


@router.get("/settings/overview")
async def get_settings_overview(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Returns a read-only snapshot of the gateway's runtime configuration:
    DLP rules, rate limits, compliance frameworks, integration status,
    and encryption state. Used by the Settings tab.
    """
    policy = load_policy()

    dlp = policy.get("dlp_rules", {})
    raw_patterns = dlp.get("patterns", {})
    rules = [
        {
            "name": name.replace("_", " ").title(),
            "severity": meta.get("severity", "unknown"),
            "description": meta.get("description", ""),
        }
        for name, meta in raw_patterns.items()
    ]

    rl = policy.get("rate_limiting", {})
    rpm = rl.get("requests_per_minute", {})

    compliance = policy.get("compliance", {})

    return {
        "dlp": {
            "enabled": dlp.get("enabled", False),
            "block_on_detection": dlp.get("block_on_detection", False),
            "redact_mode": dlp.get("redact_mode", "none"),
            "rules": rules,
        },
        "rate_limits": {
            "enabled": rl.get("enabled", False),
            "window_seconds": rl.get("window_seconds", 60),
            "per_role": {
                "admin": rpm.get("admin", 0),
                "developer": rpm.get("developer", 0),
                "auditor": rpm.get("auditor", 0),
            },
        },
        "compliance": {
            "frameworks": compliance.get("frameworks", []),
            "log_retention_days": compliance.get("log_retention_days", 90),
            "encryption_standard": compliance.get("encryption_standard", ""),
            "audit_trail_required": compliance.get("audit_trail_required", True),
        },
        "integrations": {
            "discord": bool(os.getenv("DISCORD_WEBHOOK_URL", "").strip()),
            "slack": bool(os.getenv("SLACK_WEBHOOK_URL", "").strip()),
        },
        "encryption": {
            "enabled": is_encryption_enabled(),
            "key_id": get_key_id() if is_encryption_enabled() else None,
        },
    }


@router.get("/security/encryption-status")
async def get_encryption_status(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    PSPR6 — Reports whether database encryption is active.

    Returns the current encryption state, algorithm, key version,
    and coverage so it can be included in deployment reports.
    """
    enabled = is_encryption_enabled()
    return {
        "encryption_enabled": enabled,
        "algorithm": "Fernet (AES-128-CBC + HMAC-SHA256)" if enabled else "none",
        "key_id": get_key_id() if enabled else None,
        "encrypted_fields": ["logs.message"] if enabled else [],
        "data_at_rest": enabled,
        "data_in_transit": True,
        "transit_mechanism": "HTTPS/TLS (certs/server.crt)",
        "status": "ACTIVE" if enabled else "DISABLED",
    }


@router.post("/logs/promote")
async def trigger_log_promotion(
    window_hours: int = Query(
        default=24, ge=1, le=168, description="Promotion window in hours (1–168)"
    ),
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    Log Promotion endpoint (DoD DevSecOps Monitor Phase).

    Promotes high-risk log entries (risk_score >= 0.7, severity=high)
    from the past window_hours to external monitoring channels
    (Discord/Slack/email) and writes a promotion audit record.

    Returns the number of promoted entries and their summaries.
    """
    from app.services.log_promoter import promote_logs

    promoted = await promote_logs(window_hours=window_hours)
    return {
        "promoted_at": datetime.utcnow().isoformat() + "Z",
        "window_hours": window_hours,
        "promoted_count": len(promoted),
        "promoted_entries": promoted,
    }


@router.get("/iscm/status")
async def get_iscm_status(
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
):
    """
    ISCM — Information Systems Continuous Monitoring status snapshot.

    Provides a holistic real-time view of the system's security and
    compliance posture, satisfying the DoD DevSecOps Monitor Phase
    requirement for ISCM.

    Aggregates:
    - Compliance health (HIPAA, FERPA, NIST CSF, GDPR)
    - Active threat indicators (1-hour window)
    - Log integrity (tampered entry detection)
    - Encryption and data-protection status
    - Alert integration status
    - Overall monitoring health score
    """
    now = datetime.utcnow()
    since_1h = now - timedelta(hours=1)
    since_24h = now - timedelta(hours=24)

    async with AsyncSessionLocal() as session:
        # ── Compliance: overall allow ratio across all logged endpoints ──────
        total_all = (
            await session.execute(select(func.count()).select_from(LogEntry))
        ).scalar() or 0

        total_allowed = (
            await session.execute(
                select(func.count()).where(LogEntry.policy_decision == "allow")
            )
        ).scalar() or 0

        # ── Threat indicators (last 1 hour) ──────────────────────────────────
        high_risk_1h = (
            await session.execute(
                select(func.count()).where(
                    and_(LogEntry.risk_score >= 0.7, LogEntry.created_at >= since_1h)
                )
            )
        ).scalar() or 0

        blocked_1h = (
            await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.policy_decision == "block",
                        LogEntry.created_at >= since_1h,
                    )
                )
            )
        ).scalar() or 0

        # ── Log integrity: entries that have an integrity_hash set ────────────
        total_with_hash = (
            await session.execute(
                select(func.count()).where(LogEntry.integrity_hash.isnot(None))
            )
        ).scalar() or 0

        # ── Activity (last 24 h) ─────────────────────────────────────────────
        total_24h = (
            await session.execute(
                select(func.count()).where(LogEntry.created_at >= since_24h)
            )
        ).scalar() or 0

        promotions_24h = (
            await session.execute(
                select(func.count()).where(
                    and_(
                        LogEntry.event_type == "log_promoted",
                        LogEntry.created_at >= since_24h,
                    )
                )
            )
        ).scalar() or 0

    compliance_score = round(total_allowed / total_all, 4) if total_all > 0 else 0.0
    integrity_coverage = round(total_with_hash / total_all, 4) if total_all > 0 else 1.0

    threat_level = "none"
    if high_risk_1h >= 10 or blocked_1h >= 5:
        threat_level = "high"
    elif high_risk_1h >= 3 or blocked_1h >= 2:
        threat_level = "medium"
    elif high_risk_1h >= 1 or blocked_1h >= 1:
        threat_level = "low"

    monitoring_health = "healthy"
    if compliance_score < 0.5 or threat_level == "high":
        monitoring_health = "degraded"
    elif compliance_score < 0.8 or threat_level == "medium":
        monitoring_health = "warning"

    encryption_on = is_encryption_enabled()

    return {
        "assessed_at": now.isoformat() + "Z",
        "monitoring_health": monitoring_health,
        "compliance": {
            "score": compliance_score,
            "total_events": total_all,
            "allowed_events": total_allowed,
        },
        "threat_indicators": {
            "level": threat_level,
            "high_risk_events_1h": high_risk_1h,
            "blocked_requests_1h": blocked_1h,
        },
        "log_integrity": {
            "total_entries": total_all,
            "integrity_hashed": total_with_hash,
            "coverage": integrity_coverage,
        },
        "activity_24h": {
            "total_requests": total_24h,
            "log_promotions": promotions_24h,
        },
        "data_protection": {
            "encryption_at_rest": encryption_on,
            "encryption_in_transit": True,
        },
        "alert_channels": {
            "discord": bool(os.getenv("DISCORD_WEBHOOK_URL", "").strip()),
            "slack": bool(os.getenv("SLACK_WEBHOOK_URL", "").strip()),
            "email": bool(os.getenv("ALERT_EMAIL_TO", "").strip()),
        },
    }
