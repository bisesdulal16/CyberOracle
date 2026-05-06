import asyncio
from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from sqlalchemy import select, func


async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()))
        count = result.scalar()
        print(f"Total logs in DB: {count}")

        if count > 0:
            result = await session.execute(select(LogEntry).limit(10))
            entries = result.scalars().all()
            print("\nSample entries:")
            for e in entries:
                print(
                    f"  ID={e.id}, endpoint={e.endpoint}, method={e.method}, policy_decision={e.policy_decision}, severity={e.severity}, source={e.source}, event_type={e.event_type}, risk_score={e.risk_score}"
                )


asyncio.run(check())
