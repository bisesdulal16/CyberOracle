from fastapi import APIRouter
from app.schemas.log_schema import LogEntry

router = APIRouter()

@router.get("/")
async def get_logs():
    return {"message": "Logs endpoint active"}

