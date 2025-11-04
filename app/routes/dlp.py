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
