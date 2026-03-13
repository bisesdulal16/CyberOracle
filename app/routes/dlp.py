# app/routes/dlp.py

from fastapi import APIRouter
from pydantic import BaseModel

from app.middleware.dlp_presidio import presidio_scan

router = APIRouter()


class ScanRequest(BaseModel):
    text: str


class ScanResponse(BaseModel):
    redacted: str
    entities: list[str]


@router.post("/scan", response_model=ScanResponse)
async def scan_text(payload: ScanRequest):
    """
    Scan arbitrary text for sensitive data using the Presidio DLP engine.
    Returns the redacted text and a list of detected entity types.

    Used by: Document Sanitizer, manual testing, admin tooling.
    """
    redacted, entities = presidio_scan(payload.text)
    return ScanResponse(redacted=redacted, entities=entities)
