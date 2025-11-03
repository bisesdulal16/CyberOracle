from app.db.db import AsyncSessionLocal
from app.models import LogEntry


async def log_request(
    endpoint: str, method: str, status_code: int, message: str = None
):
    """Inserts a new log entry into the 'logs' table."""
    async with AsyncSessionLocal() as session:
        entry = LogEntry(
            endpoint=endpoint, method=method, status_code=status_code, message=message
        )
        session.add(entry)
        await session.commit()
