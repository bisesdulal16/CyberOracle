"""
DLP Scan Route
--------------
Exposes the Presidio-based DLP scanner as a standalone endpoint.
Input validation applied to prevent oversized payloads.
OWASP API4: Unrestricted Resource Consumption
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from app.auth.rbac import require_roles
from app.middleware.dlp_presidio import presidio_scan
from app.services.compliance_engine import evaluate_compliance
from app.utils.logger import log_request

router = APIRouter()


class ScanRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        if len(v) > 50000:
            raise ValueError("text must not exceed 50000 characters")
        return v


class ScanResponse(BaseModel):
    redacted: str
    entities: list[str]
    frameworks: list[str]
    decision: str
    severity: str


@router.post("/scan", response_model=ScanResponse)
async def scan_text(
    payload: ScanRequest,
    _user: dict = Depends(require_roles("admin", "developer")),
):
    """
    DLP scan endpoint — admin and developer only.
    Auditors cannot trigger DLP scans.
    OWASP API1: Broken Object Level Authorization
    """
    redacted, entities = presidio_scan(payload.text)
    compliance = evaluate_compliance(payload.text, entities)

    await log_request(
        endpoint="/api/scan",
        method="POST",
        status_code=200,
        message=redacted,
        frameworks=compliance["frameworks"],
        decision=compliance["decision"],
        severity=compliance["severity"],
    )

    return ScanResponse(
        redacted=redacted,
        entities=entities,
        frameworks=compliance["frameworks"],
        decision=compliance["decision"],
        severity=compliance["severity"],
    )