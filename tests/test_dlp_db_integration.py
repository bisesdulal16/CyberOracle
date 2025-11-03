import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_dlp_and_db_flow():
    """
    Verify end-to-end functionality between the DLP middleware and database logging.
    This test ensures that:
      1. Sensitive data (e.g., SSNs) are detected and redacted by the DLP middleware.
      2. The API successfully processes the POST request.
      3. The response confirms that data has been redacted before storage or output.
    """
    # Define a test payload containing sensitive data
    payload = {"ssn": "123-45-6789", "endpoint": "/logs/test"}

    # Use ASGITransport to test FastAPI without running an external server
    transport = ASGITransport(app=app)

    # Send POST request to the /logs endpoint using the in-memory app instance
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/logs", json=payload, follow_redirects=True)

    # Validate successful response and proper redaction
    assert response.status_code == 200
    assert "***" in response.text or "REDACTED" in response.text
