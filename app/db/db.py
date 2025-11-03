import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure database URL is provided
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables.")

# Create asynchronous database engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory for database operations
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all ORM models
Base = declarative_base()
