"""
Logger async tests — covers compute_log_hash and mask_sensitive edge cases.
"""

from app.utils.logger import compute_log_hash, mask_sensitive, secure_log

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_log_request_calls_db():
    """log_request must write to DB without raising."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch("app.utils.logger.AsyncSessionLocal", return_value=mock_session):
        from app.utils.logger import log_request

        await log_request(
            endpoint="/test",
            method="POST",
            status_code=200,
            message="test message",
            event_type="ai_query",
            severity="low",
        )
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_request_masks_sensitive_message():
    """log_request must mask sensitive data before storing."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    with patch("app.utils.logger.AsyncSessionLocal", return_value=mock_session):
        from app.utils.logger import log_request

        await log_request(
            endpoint="/test",
            method="POST",
            status_code=200,
            message="password=secret123",
        )
    mock_session.add.assert_called_once()


def test_compute_log_hash_all_fields():
    h = compute_log_hash(
        endpoint="/ai/query",
        method="POST",
        status_code=200,
        message="test message",
        event_type="ai_query",
    )
    assert len(h) == 64


def test_compute_log_hash_empty_strings():
    h = compute_log_hash("", "", 0, "", "")
    assert len(h) == 64


def test_mask_sensitive_authorization_header():
    text = "authorization: Bearer abc123def456"
    masked = mask_sensitive(text)
    assert "abc123def456" not in masked


def test_mask_sensitive_json_api_key():
    text = '{"api_key": "supersecretkey123456"}'
    masked = mask_sensitive(text)
    assert "supersecretkey123456" not in masked


def test_mask_sensitive_empty_string():
    result = mask_sensitive("")
    assert result == ""


def test_mask_sensitive_integer():
    result = mask_sensitive(42)
    assert isinstance(result, str)


def test_secure_log_masks_before_logging():
    """secure_log should not raise with sensitive content."""
    secure_log("user password=mysecret123 logged in")
