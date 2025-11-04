"""
Unit Test for app/utils/alert_manager.py
----------------------------------------
Purpose:
Ensures that send_alert() behaves correctly in both environments:
 - When DISCORD_WEBHOOK_URL is NOT set → prints alert payload to stdout
 - When DISCORD_WEBHOOK_URL IS set → sends alert successfully (mocked)
"""

import io
from contextlib import redirect_stdout
from app.utils import alert_manager


def test_send_alert_prints_payload(monkeypatch):
    """
    Case 1: When no DISCORD_WEBHOOK_URL is defined,
    send_alert() should print the payload to stdout without raising exceptions.
    """
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Test alert — missing webhook",
            severity="info",
            source="unit_test",
        )

    output = buffer.getvalue()

    assert "Test alert" in output
    assert "INFO" in output.upper() or "⚠️" in output
    assert isinstance(output, str)


def test_send_alert_with_mocked_webhook(monkeypatch):
    """
    Case 2: When DISCORD_WEBHOOK_URL is defined,
    send_alert() should attempt to send (mocked) without raising exceptions.
    """
    # Mock Discord webhook URL (no real request sent)
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://mock.discord.webhook")

    # Mock requests.post to prevent real network call
    def mock_post(url, json):
        assert "content" in json
        # Return a fake successful response

        class Response:
            status_code = 204

        return Response()

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    # Run and ensure no exception occurs
    alert_manager.send_alert(
        "Mocked Discord alert",
        severity="warning",
        source="unit_test",
    )
