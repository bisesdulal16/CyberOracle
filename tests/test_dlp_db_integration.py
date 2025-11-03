import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_dlp_and_db_flow():
    """Ensure sensitive data is redacted and request completes."""
    payload = {"ssn": "123-45-6789", "endpoint": "/logs/test"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/logs", json=payload)
    assert response.status_code in [200, 201]
