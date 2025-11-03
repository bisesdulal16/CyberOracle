from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log_request

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


@router.post("/ingest")
async def ingest_logs(request: Request):
    """
    Receive logs and save them asynchronously to the database.
    """
    data = await request.json()
    await log_request("/logs/ingest", "POST", 200, str(data))
    return JSONResponse({"message": "Log stored successfully"})
