"""
Logs API Router
---------------
Provides endpoints for log ingestion and verification.

Security Notes (OWASP-ASVS 9.2):
- Input must not contain unmasked sensitive data.
- Always mask values BEFORE storing or logging.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.schemas.log_schema import LogIngest
from app.utils.db_encryption import decrypt_value
from app.utils.logger import log_request, mask_sensitive, secure_log

# UPDATED: combined RBAC imports and added permission-based RBAC
from app.auth.rbac import require_roles, require_permission

router = APIRouter()


@router.get("/")
async def get_logs():
    """
    Health check for the logs endpoint.
    """
    return {"message": "Logs endpoint active"}


@router.get("/list")
async def list_logs(
    # ADDED: RBAC enforcement so only roles with view_all_logs permission can access logs
    _user: dict = Depends(require_permission("view_all_logs")),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    policy_decision: Optional[str] = Query(default=None),
):
    """
    Paginated log retrieval for the Audit Log panel.

    Query params
    ------------
    limit          : records per page (1–200, default 50)
    offset         : records to skip (for pagination)
    severity       : filter by "low" | "medium" | "high"
    event_type     : filter by "ai_query" | "ai_query_blocked" | "dlp_alert" etc.
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

    return {
        "logs": [
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
                # Decrypt message at read time if encryption is active
                "message": decrypt_value(e.message) if e.message else None,
                "created_at": e.created_at.isoformat() + "Z" if e.created_at else None,
            }
            for e in entries
        ],
        "count": len(entries),
        "offset": offset,
        "limit": limit,
    }


@router.post("/")
async def create_log(request: Request):
    """
    Temporary POST handler to simulate log ingestion for testing.

    Notes
    -----
    This returns the masked body to the caller.
    Useful for verifying masking works.
    """
    body = await request.json()
    masked = mask_sensitive(str(body))
    secure_log(f"Received simulated log payload: {masked}")

    return {"received": body, "masked_representation": masked}


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
    # Convert incoming model to dict
    data = payload.model_dump()

    # Mask before database storage
    masked_msg = mask_sensitive(str(data))

    # Log to stdout (masked)
    secure_log(f"Ingested log: {masked_msg}")

    # Insert into database
    await log_request(
        endpoint="/logs/ingest",
        method="POST",
        status_code=200,
        message=masked_msg,
    )

    return JSONResponse({"message": "Log stored successfully"})
