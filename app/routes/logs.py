"""
Logs API Router
---------------
Provides endpoints for log ingestion and retrieval.

Security Notes (OWASP-ASVS 9.2):
- Input must not contain unmasked sensitive data.
- Always mask values BEFORE storing or logging.
- Query parameters validated against allowlists to prevent injection.
- Integrity hashes verified on read to detect tampered entries.
"""

from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.schemas.log_schema import LogIngest
from app.utils.db_encryption import decrypt_value
from app.utils.logger import compute_log_hash, log_request, mask_sensitive, secure_log

from app.auth.rbac import require_roles, require_permission

router = APIRouter()


@router.get("/")
async def get_logs(_: dict = Depends(require_permission("view_all_logs"))):
    return {"message": "Logs endpoint active"}


@router.get("/list")
async def list_logs(
    _user: dict = Depends(require_permission("view_all_logs")),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    # Allowlist validation — only accepted values pass through
    # OWASP API3: Prevents injection via free-text query parameters
    severity: Optional[Literal["low", "medium", "high"]] = Query(default=None),
    event_type: Optional[
        Literal[
            "ai_query",
            "ai_query_blocked",
            "dlp_alert",
            "document_sanitize",
            "ai_query_model_error",
        ]
    ] = Query(default=None),
    policy_decision: Optional[Literal["allow", "redact", "block"]] = Query(
        default=None
    ),
):
    """
    Paginated log retrieval for the Audit Log panel.

    - Decrypts message field at read time if encryption is active.
    - Verifies integrity_hash on each entry and flags tampered records.

    Query params
    ------------
    limit          : records per page (1-200, default 50)
    offset         : records to skip (for pagination)
    severity       : filter by "low" | "medium" | "high"
    event_type     : filter by allowed event type values only
    policy_decision: filter by "allow" | "redact" | "block"
    """
    async with AsyncSessionLocal() as session:
        query = select(LogEntry).order_by(LogEntry.created_at.desc())

        if severity:
            query = query.where(LogEntry.severity == severity)
        if event_type:
            query = query.where(LogEntry.event_type == event_type)
        if policy_decision:
            query = query.where(LogEntry.policy_decision == policy_decision)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        entries = result.scalars().all()

    logs = []
    for e in entries:
        # Decrypt message at read time if encryption is active
        decrypted_message = decrypt_value(e.message) if e.message else None

        # Verify integrity hash to detect tampered entries (OWASP-ASVS 9.5)
        tampered = False
        if e.integrity_hash:
            expected_hash = compute_log_hash(
                endpoint=e.endpoint,
                method=e.method,
                status_code=e.status_code,
                message=decrypted_message,
                event_type=e.event_type,
            )
            tampered = expected_hash != e.integrity_hash

        logs.append(
            {
                "id": e.id,
                "endpoint": e.endpoint,
                "method": e.method,
                "status_code": e.status_code,
                "event_type": e.event_type,
                "severity": e.severity,
                "risk_score": e.risk_score,
                "source": e.source,
                "policy_decision": e.policy_decision,
                "message": decrypted_message,
                "created_at": e.created_at.isoformat() + "Z" if e.created_at else None,
                # None = pre-dates integrity hashing, True = verified, False = TAMPERED
                "integrity_verified": (not tampered) if e.integrity_hash else None,
            }
        )

    return {
        "logs": logs,
        "count": len(logs),
        "offset": offset,
        "limit": limit,
    }


@router.post("/")
async def create_log(
    request: Request,
    _user: dict = Depends(require_roles("admin", "developer")),
):
    """
    Log ingestion test endpoint. Protected — requires admin or developer role.
    Returns only the masked representation, never the raw body.
    OWASP API1: Broken Object Level Authorization
    """
    body = await request.json()
    masked = mask_sensitive(str(body))
    secure_log(f"Received log payload: {masked}")
    return {"masked_representation": masked}


@router.post("/ingest")
async def ingest_logs(
    payload: LogIngest,
    _user: dict = Depends(require_roles("admin", "developer")),
):
    """
    Main endpoint for log ingestion.
    Stores masked logs in the database.

    Security Notes (OWASP-ASVS 9.1):
    --------------------------------
    input → mask_sensitive → log_request → DB insert
    """
    data = payload.model_dump()
    masked_msg = mask_sensitive(str(data))
    secure_log(f"Ingested log: {masked_msg}")

    await log_request(
        endpoint="/logs/ingest",
        method="POST",
        status_code=200,
        message=masked_msg,
    )

    return JSONResponse({"message": "Log stored successfully"})
