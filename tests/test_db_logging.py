import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models import LogEntry
from app.db.db import AsyncSessionLocal, Base, DATABASE_URL

# -------------------- FIXTURES --------------------


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a single shared event loop for all async tests.
    This resolves macOS and asyncpg issues where multiple event loops
    cause 'Future attached to a different loop' errors.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    """
    Set up the test database schema before running tests.
    - Creates all tables defined in Base.metadata
    - Drops all tables after tests complete
    Ensures a clean database state for each test module.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create all tables before running tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Run the actual tests here

    # Drop all tables after the tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose the engine to close all connections
    await engine.dispose()


@pytest.fixture
async def session():
    """
    Provides a new AsyncSession for each test.
    Ensures transactions are rolled back and sessions closed properly
    to avoid dangling connections or loop teardown errors.
    """
    async with AsyncSessionLocal() as session:
        yield session
        # Handle teardown safely to avoid RuntimeError after event loop closes
        try:
            await session.rollback()
        except RuntimeError:
            pass
        try:
            await session.close()
        except RuntimeError:
            pass


# -------------------- TESTS --------------------


@pytest.mark.asyncio
async def test_database_connection():
    """
    Verify that the database engine can connect successfully.
    Confirms the connection string and Postgres service are valid.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        assert conn is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_log_entry_insertion(session: AsyncSession):
    """
    Test log entry creation and commit behavior.
    - Inserts a dummy LogEntry into the logs table
    - Commits and refreshes the object
    - Verifies that an ID is generated and fields are stored correctly
    """
    # Create a new log entry record
    entry = LogEntry(
        endpoint="/test",
        method="POST",
        status_code=201,
        message="Test log insert",
    )

    # Add and commit to the database
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    # Validate that the record was persisted correctly
    assert entry.id is not None
    assert entry.endpoint == "/test"
    assert entry.status_code == 201
