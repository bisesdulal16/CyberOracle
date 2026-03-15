"""
Alert Manager Utility
---------------------
Handles alert dispatching to Discord and Slack webhooks.
If a webhook is not configured, prints the payload instead (useful for testing).

Environment variables
---------------------
DISCORD_WEBHOOK_URL  — Discord Incoming Webhook URL  (optional)
SLACK_WEBHOOK_URL    — Slack Incoming Webhook URL     (optional)
"""

import os
import requests
from datetime import datetime, timezone


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def _send_discord(formatted_message: str) -> None:
    """Dispatch an alert to the configured Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("[!] Discord webhook not set. Payload:\n" + formatted_message)
        return
    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL, json={"content": formatted_message}, timeout=5
        )
        if resp.status_code == 204:
            print("[+] Discord alert sent.")
        else:
            print(f"[!] Discord alert failed: HTTP {resp.status_code}")
    except Exception as exc:
        print(f"[!] Discord alert error: {exc}")


def _send_slack(formatted_message: str) -> None:
    """Dispatch an alert to the configured Slack Incoming Webhook."""
    if not SLACK_WEBHOOK_URL:
        print("[!] Slack webhook not set. Payload:\n" + formatted_message)
        return
    try:
        # Slack Incoming Webhooks expect {"text": "..."} JSON body
        resp = requests.post(
            SLACK_WEBHOOK_URL, json={"text": formatted_message}, timeout=5
        )
        if resp.status_code == 200:
            print("[+] Slack alert sent.")
        else:
            print(f"[!] Slack alert failed: HTTP {resp.status_code}")
    except Exception as exc:
        print(f"[!] Slack alert error: {exc}")


def send_alert(message: str, severity: str = "info", source: str = "system"):
    """
    Send an alert message to Discord and Slack.
    Channels with no webhook URL configured are silently skipped
    (a console notice is printed instead, which is useful for CI / local dev).

    Parameters
    ----------
    message  : Human-readable alert body.
    severity : "info" | "warning" | "high" | "critical"
    source   : Originating component (e.g. "ai_route", "dlp_middleware").

    Returns
    -------
    The formatted message string (useful for test assertions).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_message = (
        f"[CyberOracle] {severity.upper()} alert from {source}\n"
        f"{message}\n"
        f"Time: {timestamp}"
    )

    _send_discord(formatted_message)
    _send_slack(formatted_message)

    return formatted_message
