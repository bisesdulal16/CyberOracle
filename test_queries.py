import asyncio
from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from sqlalchemy import select, func, text

async def test_queries():
    async with AsyncSessionLocal() as session:
        # Query 1: Total Requests (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        total = result.scalar()
        print(f"1. Total Requests (24h): {total}")

        # Query 2: Blocked Requests (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.policy_decision == 'block',
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        blocked = result.scalar()
        print(f"2. Blocked Requests (24h): {blocked}")

        # Query 3: Redacted Requests (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.policy_decision == 'redact',
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        redacted = result.scalar()
        print(f"3. Redacted Requests (24h): {redacted}")

        # Query 4: High Severity Events (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.severity == 'high',
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        high_severity = result.scalar()
        print(f"4. High Severity Events (24h): {high_severity}")

        # Query 5: HIPAA-Related Events (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.frameworks.like('%HIPAA%'),
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        hipaa = result.scalar()
        print(f"5. HIPAA-Related Events (24h): {hipaa}")

        # Query 6: FERPA-Related Events (24h)
        result = await session.execute(
            select(func.count()).where(
                LogEntry.frameworks.like('%FERPA%'),
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        ferpa = result.scalar()
        print(f"6. FERPA-Related Events (24h): {ferpa}")

        # Query 7: Policy Decisions Distribution
        result = await session.execute(
            text("SELECT policy_decision AS label, COUNT(*)::bigint AS value FROM logs WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY policy_decision")
        )
        print("\n7. Policy Decisions Distribution:")
        for row in result:
            print(f"   {row}")

        # Query 8: Policy Decisions Over Time
        result = await session.execute(
            text("SELECT date_trunc('minute', created_at) AS time, COUNT(*)::bigint AS value FROM logs WHERE policy_decision IN ('allow', 'redact', 'block') AND created_at >= NOW() - INTERVAL '24 hours' GROUP BY 1 ORDER BY 1 LIMIT 10")
        )
        print("\n8. Policy Decisions Over Time (first 10):")
        for row in result:
            print(f"   {row}")

        # Query 9: HIPAA Events Over Time
        result = await session.execute(
            text("SELECT date_trunc('minute', created_at) AS time, COUNT(*)::bigint AS value FROM logs WHERE frameworks LIKE '%HIPAA%' AND created_at >= NOW() - INTERVAL '24 hours' GROUP BY 1 ORDER BY 1 LIMIT 10")
        )
        print("\n9. HIPAA Events Over Time (first 10):")
        for row in result:
            print(f"   {row}")

        # Query 10: FERPA Events Over Time
        result = await session.execute(
            text("SELECT date_trunc('minute', created_at) AS time, COUNT(*)::bigint AS value FROM logs WHERE frameworks LIKE '%FERPA%' AND created_at >= NOW() - INTERVAL '24 hours' GROUP BY 1 ORDER BY 1 LIMIT 10")
        )
        print("\n10. FERPA Events Over Time (first 10):")
        for row in result:
            print(f"   {row}")

        # Query 11: High Severity Events Over Time
        result = await session.execute(
            text("SELECT date_trunc('minute', created_at) AS time, COUNT(*)::bigint AS value FROM logs WHERE severity = 'high' AND created_at >= NOW() - INTERVAL '24 hours' GROUP BY 1 ORDER BY 1 LIMIT 10")
        )
        print("\n11. High Severity Events Over Time (first 10):")
        for row in result:
            print(f"   {row}")

        # Query 15: Total Alerts Triggered (24h)
        result = await session.execute(
            select(func.count()).where(
                (LogEntry.severity == 'high') | (LogEntry.risk_score >= 0.7),
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            )
        )
        alerts = result.scalar()
        print(f"15. Total Alerts Triggered (24h): {alerts}")

        # Check all entries created in last 24h
        result = await session.execute(
            select(LogEntry).where(
                LogEntry.created_at >= text("NOW() - INTERVAL '24 hours'")
            ).order_by(LogEntry.created_at.desc())
        )
        recent = result.scalars().all()
        print(f"\nRecent entries (last 24h): {len(recent)}")
        for e in recent:
            print(f"  ID={e.id}, endpoint={e.endpoint}, policy_decision={e.policy_decision}, severity={e.severity}, frameworks={e.frameworks}")

asyncio.run(test_queries())