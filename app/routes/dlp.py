# app/routes/dlp.py for test

from fastapi import APIRouter, Body
from app.middleware.dlp_presidio import presidio_scan

router = APIRouter()


@router.post("/scan")
async def scan_text(payload: dict = Body(...)):
    """
    Accepts JSON like {"text": "some content"} and returns
    redacted text + detected entities.
    """
    text = payload.get("text", "")
    redacted, entities = presidio_scan(text)
    return {"redacted": redacted, "entities": entities}


@router.post("/analyze")
async def analyze_text(payload: dict = Body(...)):
    """
    New required endpoint for test suite compatibility.

    IMPORTANT:
    The DLP middleware intercepts and blocks sensitive input
    BEFORE this handler runs.

    If middleware blocks: returns 400 (expected in tests)
    If clean input: this handler returns 200 OK with echo.
    """
    text = payload.get("text", "")
    return {"message": "Text is clean", "received": text}
