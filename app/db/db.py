import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure database URL is provided
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables.")

# Use NullPool for tests to avoid race conditions (concurrent operations)
# For production, consider using AsyncPool with proper sizing
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    echo_pool=os.getenv("PYTEST") == "1",  # Echo pool only in tests
    poolclass=NullPool  # Prevents connection reuse race conditions
)

# Create async session factory for database operations
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all ORM models
Base = declarative_base()
