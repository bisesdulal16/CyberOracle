import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.db import Base, DATABASE_URL
from app.models import LogEntry


@pytest_asyncio.fixture(scope="module")
async def engine():
    """
    Create an isolated async engine for this test module.

    NullPool avoids connection reuse issues like:
    'cannot perform operation: another operation is in progress'
    """
    test_engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    """
    Provide a fresh AsyncSession for each test, bound to the isolated engine.
    """
    TestingSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestingSessionLocal() as db_session:
        yield db_session

        # Safe teardown: only rollback if the session is still active.
        try:
            if db_session.in_transaction():
                await db_session.rollback()
        except (RuntimeError, Exception):
            pass


@pytest.mark.asyncio
async def test_database_connection(engine):
    """
    Verify that the database engine can connect successfully.
    """
    async with engine.begin() as conn:
        assert conn is not None


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
