"""
Database Initialization Script
------------------------------
Creates database tables from SQLAlchemy models.

Required because the project uses AsyncEngine (asyncpg).
"""

import asyncio

from app.db.db import engine, Base


async def init_db():
    async with engine.begin() as conn:
        # Run table creation
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(init_db())
