"""
Alert Manager Tests
--------------------
Tests for the alert dispatch utility.
Verifies formatting and no-webhook fallback behavior.
"""

from unittest.mock import patch, MagicMock
from app.utils.alert_manager import send_alert, _send_discord, _send_slack


def test_send_alert_returns_formatted_message():
    msg = send_alert("Test alert", severity="high", source="test")
    assert "[CyberOracle]" in msg
    assert "HIGH" in msg
    assert "Test alert" in msg
    assert "test" in msg


def test_send_alert_default_severity():
    msg = send_alert("Default severity alert")
    assert "INFO" in msg


def test_send_alert_includes_timestamp():
    msg = send_alert("Timestamp test")
    assert "UTC" in msg


def test_send_discord_no_webhook_prints(capsys):
    _send_discord("test message")
    captured = capsys.readouterr()
    assert "Discord webhook not set" in captured.out


def test_send_slack_no_webhook_prints(capsys):
    _send_slack("test message")
    captured = capsys.readouterr()
    assert "Slack webhook not set" in captured.out


def test_send_discord_with_webhook_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    with patch("app.utils.alert_manager.DISCORD_WEBHOOK_URL", "https://discord.test"):
        with patch("requests.post", return_value=mock_resp):
            _send_discord("test")


def test_send_discord_with_webhook_failure(capsys):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    with patch("app.utils.alert_manager.DISCORD_WEBHOOK_URL", "https://discord.test"):
        with patch("requests.post", return_value=mock_resp):
            _send_discord("test")
    captured = capsys.readouterr()
    assert "failed" in captured.out


def test_send_slack_with_webhook_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("app.utils.alert_manager.SLACK_WEBHOOK_URL", "https://slack.test"):
        with patch("requests.post", return_value=mock_resp):
            _send_slack("test")


def test_send_slack_with_webhook_failure(capsys):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    with patch("app.utils.alert_manager.SLACK_WEBHOOK_URL", "https://slack.test"):
        with patch("requests.post", return_value=mock_resp):
            _send_slack("test")
    captured = capsys.readouterr()
    assert "failed" in captured.out


def test_send_discord_exception_handled(capsys):
    with patch("app.utils.alert_manager.DISCORD_WEBHOOK_URL", "https://discord.test"):
        with patch("requests.post", side_effect=Exception("connection error")):
            _send_discord("test")
    captured = capsys.readouterr()
    assert "error" in captured.out.lower()


def test_send_slack_exception_handled(capsys):
    with patch("app.utils.alert_manager.SLACK_WEBHOOK_URL", "https://slack.test"):
        with patch("requests.post", side_effect=Exception("connection error")):
            _send_slack("test")
    captured = capsys.readouterr()
    assert "error" in captured.out.lower()
