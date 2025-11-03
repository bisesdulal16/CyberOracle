import pytest
from app.models import LogEntry
from app.db.db import AsyncSessionLocal, Base, engine

@pytest.mark.asyncio
async def test_database_connection():
    """Ensure database engine connects successfully."""
    async with engine.begin() as conn:
        assert conn is not None

@pytest.mark.asyncio
async def test_log_entry_insertion():
    """Verify that LogEntry objects can be added to the database."""
    async with AsyncSessionLocal() as session:
        entry = LogEntry(
            endpoint="/test",
            method="POST",
            status_code=201,
            message="Test log insert"
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        assert entry.id is not None
        assert entry.endpoint == "/test"
