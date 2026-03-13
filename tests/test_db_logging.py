import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.db import AsyncSessionLocal, Base, DATABASE_URL
from app.models import LogEntry


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    """
    Set up the test database schema before running tests.
    Creates all tables before tests and drops them afterward.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session():
    """
    Provides a fresh AsyncSession for each test.
    """
    async with AsyncSessionLocal() as session:
        yield session
        try:
            await session.rollback()
        except RuntimeError:
            pass
        try:
            await session.close()
        except RuntimeError:
            pass


@pytest.mark.asyncio
async def test_database_connection():
    """
    Verify that the database engine can connect successfully.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        assert conn is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_log_entry_insertion(session: AsyncSession):
    """
    Test log entry creation and commit behavior.
    """
    entry = LogEntry(
        endpoint="/test",
        method="POST",
        status_code=201,
        message="Test log insert",
    )

    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    assert entry.id is not None
    assert entry.endpoint == "/test"
    assert entry.status_code == 201
