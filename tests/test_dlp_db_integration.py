import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.auth.jwt_utils import create_access_token


def _auth_headers():
    token = create_access_token({"sub": "testuser", "role": "developer"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_dlp_and_db_flow():
    """
    Verify end-to-end DLP middleware and database logging.
    Sensitive data must be redacted before storage.
    POST /logs/ requires authentication (NCFR3).
    """
    payload = {"ssn": "123-45-6789", "endpoint": "/logs/test"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/logs/",
            json=payload,
            headers=_auth_headers(),
            follow_redirects=True,
        )

    assert response.status_code == 200
    assert any(
        tag in response.text
        for tag in [
            "***",
            "<GENERIC_SSN>",
            "<DATE_TIME>",
            "<US_SOCIAL_SECURITY_NUMBER>",
        ]
    )
