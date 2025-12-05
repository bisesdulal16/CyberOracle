from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from app.utils.logger import log_request, secure_log, mask_sensitive
from app.schemas.log_schema import LogIngest
from app.auth.dependencies import get_current_user, api_key_required, require_role

router = APIRouter()


# Existing endpoints remain unchanged
@router.get("/")
async def get_logs():
    return {"message": "Logs endpoint active"}


@router.post("/")
async def create_log(request: Request):
    body = await request.json()
    masked = mask_sensitive(str(body))
    secure_log(f"Received simulated log payload: {masked}")
    return {"received": body, "masked_representation": masked}


# Updated ingest endpoint
@router.post("/ingest")
async def ingest_logs(
    payload: LogIngest,
    user: dict = Depends(get_current_user),  # JWT validation
    api_key: str = Depends(api_key_required),  # API key validation
    admin: dict = Depends(require_role("admin")),  # Optional: restrict to admin users
):
    """
    Main endpoint for log ingestion.
    Stores masked logs in the database.

    Security Notes:
    - JWT validated
    - API key validated
    - Optional RBAC (admin only)
    - Input → mask_sensitive → log_request → DB insert
    """
    data = payload.model_dump()

    # Mask before storing/logging
    masked_msg = mask_sensitive(str(data))

    # Log to stdout
    secure_log(f"Ingested log: {masked_msg}")

    # Insert into database
    await log_request(
        endpoint="/logs/ingest",
        method="POST",
        status_code=200,
        message=masked_msg,
    )

    return JSONResponse({"message": "Log stored successfully"})
