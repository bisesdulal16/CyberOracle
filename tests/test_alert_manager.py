"""
Unit tests for app/utils/alert_manager.py
"""

import io
import smtplib
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from app.utils import alert_manager


def test_send_alert_prints_payload_when_no_webhooks(monkeypatch):
    """
    When neither webhook is configured, send_alert() should print
    the formatted payload for both Discord and Slack paths.
    """
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        formatted = alert_manager.send_alert(
            "Test alert — missing webhooks",
            severity="info",
            source="unit_test",
        )

    output = buffer.getvalue()

    assert "[!] Discord webhook not set" in output
    assert "[!] Slack webhook not set" in output
    assert "Test alert — missing webhooks" in output
    assert "INFO alert from unit_test" in formatted
    assert "Time:" in formatted


def test_send_discord_success(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", "https://mock.discord")
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)

    def mock_post(url, json=None, timeout=None):
        assert url == "https://mock.discord"
        assert "content" in json
        assert timeout == 5

        class Response:
            status_code = 204

        return Response()

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Mocked Discord alert",
            severity="warning",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[+] Discord alert sent." in output


def test_send_discord_failure_status(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", "https://mock.discord")
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)

    def mock_post(url, json=None, timeout=None):
        class Response:
            status_code = 500

        return Response()

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Discord should fail",
            severity="high",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[!] Discord alert failed: HTTP 500" in output


def test_send_discord_exception(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", "https://mock.discord")
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)

    def mock_post(url, json=None, timeout=None):
        raise RuntimeError("discord down")

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Discord exception",
            severity="critical",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[!] Discord alert error: discord down" in output


def test_send_slack_success(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", "https://mock.slack")

    def mock_post(url, json=None, timeout=None):
        assert url == "https://mock.slack"
        assert "text" in json
        assert timeout == 5

        class Response:
            status_code = 200

        return Response()

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Mocked Slack alert",
            severity="warning",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[+] Slack alert sent." in output


def test_send_slack_failure_status(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", "https://mock.slack")

    def mock_post(url, json=None, timeout=None):
        class Response:
            status_code = 500

        return Response()

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Slack should fail",
            severity="high",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[!] Slack alert failed: HTTP 500" in output


def test_send_slack_exception(monkeypatch):
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", "https://mock.slack")

    def mock_post(url, json=None, timeout=None):
        raise RuntimeError("slack down")

    monkeypatch.setattr(alert_manager.requests, "post", mock_post)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(
            "Slack exception",
            severity="critical",
            source="unit_test",
        )

    output = buffer.getvalue()
    assert "[!] Slack alert error: slack down" in output


# ---------------------------------------------------------------------------
# _send_email tests
# ---------------------------------------------------------------------------


def _patch_email_vars(monkeypatch, *, configured: bool):
    """Helper: set or clear the four required email env vars on the module."""
    if configured:
        monkeypatch.setattr(alert_manager, "ALERT_EMAIL_FROM", "from@example.com")
        monkeypatch.setattr(alert_manager, "ALERT_EMAIL_TO", "to@example.com")
        monkeypatch.setattr(alert_manager, "SMTP_USER", "user@example.com")
        monkeypatch.setattr(alert_manager, "SMTP_PASSWORD", "secret")
    else:
        monkeypatch.setattr(alert_manager, "ALERT_EMAIL_FROM", None)
        monkeypatch.setattr(alert_manager, "ALERT_EMAIL_TO", None)
        monkeypatch.setattr(alert_manager, "SMTP_USER", None)
        monkeypatch.setattr(alert_manager, "SMTP_PASSWORD", None)


def test_send_email_not_configured(monkeypatch):
    """Skips email gracefully and prints a notice when credentials are absent."""
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)
    _patch_email_vars(monkeypatch, configured=False)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert("no email config", severity="info", source="test")

    assert "[!] Email alert not configured" in buffer.getvalue()


def test_send_email_success(monkeypatch):
    """Sends email and prints success when credentials are present."""
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)
    _patch_email_vars(monkeypatch, configured=True)

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.utils.alert_manager.smtplib.SMTP", mock_smtp_cls):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            alert_manager.send_alert(
                "email success test", severity="high", source="test"
            )

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.send_message.assert_called_once()
    assert "[+] Email alert sent." in buffer.getvalue()


def test_send_email_exception(monkeypatch):
    """Catches SMTP exceptions and prints an error message."""
    monkeypatch.setattr(alert_manager, "DISCORD_WEBHOOK_URL", None)
    monkeypatch.setattr(alert_manager, "SLACK_WEBHOOK_URL", None)
    _patch_email_vars(monkeypatch, configured=True)

    with patch(
        "app.utils.alert_manager.smtplib.SMTP",
        side_effect=smtplib.SMTPException("conn refused"),
    ):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            alert_manager.send_alert("email error test", severity="high", source="test")

    assert "[!] Email alert error: conn refused" in buffer.getvalue()
