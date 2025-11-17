"""
Logs API Router
---------------
Provides endpoints for log ingestion and verification.

Security Notes (OWASP-ASVS 9.2):
- Input must not contain unmasked sensitive data.
- Always mask values BEFORE storing or logging.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log_request, secure_log, mask_sensitive
from app.schemas.log_schema import LogIngest  # NEW

router = APIRouter()


@router.get("/")
async def get_logs():
    """
    Simple health check for logs endpoint.
    """
    return {"message": "Logs endpoint active"}


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
async def ingest_logs(payload: LogIngest):
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
