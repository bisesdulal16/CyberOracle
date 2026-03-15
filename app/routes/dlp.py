# app/routes/dlp.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.dlp_presidio import presidio_scan
from app.auth.rbac import require_roles

router = APIRouter()


class ScanRequest(BaseModel):
    text: str


class ScanResponse(BaseModel):
    redacted: str
    entities: list[str]


@router.post("/scan", response_model=ScanResponse)
async def scan_text(
    payload: ScanRequest,
    _user: dict = Depends(require_roles("admin", "developer")),
):
    """
    Scan arbitrary text for sensitive data using the Presidio DLP engine.
    Returns the redacted text and a list of detected entity types.

    Used by: Document Sanitizer, manual testing, admin tooling.
    """
    redacted, entities = presidio_scan(payload.text)
    return ScanResponse(redacted=redacted, entities=entities)
