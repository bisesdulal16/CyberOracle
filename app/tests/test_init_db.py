"""
Database Init Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_init_db_runs():
    """init_db must call create_all without raising."""
    mock_conn = AsyncMock()
    mock_conn.run_sync = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.db.init_db.engine") as mock_engine:
        mock_engine.begin.return_value = mock_ctx
        from app.db.init_db import init_db
        await init_db()

    mock_conn.run_sync.assert_called_once()
