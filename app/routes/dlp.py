"""
This is test code (wull be updated later)
DLP Routes for CyberOracle
--------------------------
Provides endpoints to scan text or uploaded files for sensitive information
using the Presidio analyzer.
"""

from fastapi import APIRouter, Request, UploadFile, File
from app.middleware.dlp_presidio import presidio_scan

router = APIRouter()


@router.post("/scan-text")
async def scan_text(request: Request):
    """
    Accepts JSON input with 'text' field and returns detected entities and redacted text.
    Example input: {"text": "My SSN is 219-09-9999 and my email is test@example.com"}
    """
    body = await request.json()
    text = body.get("text", "")

    redacted, entities = presidio_scan(text)
    return {
        "input_text": text,
        "redacted_text": redacted,
        "detected_entities": entities,
    }


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts a .txt file upload and scans its contents for sensitive information.
    Returns the detected entities and a redacted text preview.
    """
    content = await file.read()
    text = content.decode("utf-8")

    redacted, entities = presidio_scan(text)
    return {
        "filename": file.filename,
        "detected_entities": entities,
        "redacted_preview": redacted[:300],
        "entity_count": len(entities),
    }
