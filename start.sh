#!/bin/bash
# CyberOracle startup script
# Run this once to start everything: ./start.sh

set -e
cd "$(dirname "$0")"
source venv/bin/activate

echo "[1/3] Creating DB tables if they don't exist..."
python3 -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from app.db.db import engine, Base
from app.models import LogEntry  # registers LogEntry with Base
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('  Tables ready.')
asyncio.run(init())
"

echo "[2/3] Freeing port 8001 if already in use..."
lsof -ti :8001 | xargs -r kill -9 2>/dev/null && sleep 1 || true

echo "[3/3] Starting uvicorn backend on port 8001..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
