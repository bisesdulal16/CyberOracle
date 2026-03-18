"""
Unit tests for app/utils/alert_manager.py
"""

import io
from contextlib import redirect_stdout

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
