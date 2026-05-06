from fastapi import APIRouter
from pydantic import BaseModel

from app.middleware.dlp_presidio import presidio_scan
from app.services.compliance_engine import evaluate_compliance
from app.utils.logger import log_request

router = APIRouter()


class ScanRequest(BaseModel):
    text: str


class ScanResponse(BaseModel):
    redacted: str
    entities: list[str]
    frameworks: list[str]
    decision: str
    severity: str


@router.post("/scan", response_model=ScanResponse)
async def scan_text(payload: ScanRequest):
    redacted, entities = presidio_scan(payload.text)
    compliance = evaluate_compliance(payload.text, entities)

    await log_request(
        endpoint="/api/scan",
        method="POST",
        status_code=200,
        message=redacted,  # We save the REDACTED version
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
