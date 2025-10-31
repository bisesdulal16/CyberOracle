"""
Unit Test for app/utils/alert_manager.py
----------------------------------------
Purpose:
Ensures that the send_alert() function executes without raising
errors and prints the expected payload when no webhook is set.
"""

import builtins
import json
import io
from contextlib import redirect_stdout
from app.utils import alert_manager


def test_send_alert_prints_payload(monkeypatch):
    """
    When no SLACK_WEBHOOK_URL is defined, send_alert() should print
    the alert payload to stdout without raising exceptions.
    """

    # Simulate environment variable not being set
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    # Capture printed output
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        alert_manager.send_alert(["ssn", "credit_card"])

    output = buffer.getvalue()

    # Validate the printed payload contains expected text
    assert "ssn" in output or "credit_card" in output
    assert "⚠️" in output
    assert isinstance(output, str)
