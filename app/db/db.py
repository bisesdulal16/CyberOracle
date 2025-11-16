import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# Detect GitHub Actions
CI_ENV = os.getenv("CI") == "true"

# Local default DB (no external services)
LOCAL_DEFAULT_DB = "sqlite+aiosqlite:///./test.db"

# 1. Load DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. If missing locally, use SQLite
if not DATABASE_URL and not CI_ENV:
    DATABASE_URL = LOCAL_DEFAULT_DB

# 3. If running in GitHub Actions but still missing, fallback to Postgres
if CI_ENV and not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/cyberoracle"

# Final safety
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set and no fallback could be applied.")

# Create async database engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Base ORM class
Base = declarative_base()
