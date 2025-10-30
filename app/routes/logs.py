from fastapi import APIRouter
from app.schemas.log_schema import LogEntry

router = APIRouter()

@router.get("/")
async def get_logs():
    """Simple health check for logs endpoint."""
    return {"message": "Logs endpoint active"}

@router.post("/")
async def create_log(request: Request):
    """
    Temporary POST handler to simulate log ingestion.
    Accepts JSON payload and returns the (possibly redacted) body.
    """
    body = await request.json()
    return {"received": body}

