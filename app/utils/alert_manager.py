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
import smtplib
from email.mime.text import MIMEText

import requests
from datetime import datetime, timezone


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


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


def _send_email(formatted_message: str) -> None:
    """Dispatch an alert via SMTP email."""
    if not all([ALERT_EMAIL_FROM, ALERT_EMAIL_TO, SMTP_USER, SMTP_PASSWORD]):
        print("[!] Email alert not configured. Skipping email.")
        return
    try:
        msg = MIMEText(formatted_message, "plain")
        msg["Subject"] = "[CyberOracle] Security Alert"
        msg["From"] = ALERT_EMAIL_FROM
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print("[+] Email alert sent.")
    except Exception as exc:
        print(f"[!] Email alert error: {exc}")


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
    _send_email(formatted_message)

    return formatted_message
