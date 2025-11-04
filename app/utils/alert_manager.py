"""
Alert Manager Utility
---------------------
Handles alert dispatching to Discord webhooks.
If webhook is not configured, prints the payload instead (useful for testing).
"""

import os
import requests
from datetime import datetime


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_alert(message: str, severity: str = "info", source: str = "system"):
    """
    Sends an alert message to Discord or prints it if webhook is not set.
    Includes timestamp and severity for observability.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_message = (
        f"⚠️ {severity.upper()} alert from {source}\n" f"{message}\n\n🕒 {timestamp}"
    )

    # --- CI-friendly mode: no webhook available ---
    if not DISCORD_WEBHOOK_URL:
        print(
            "[!] Discord webhook not set in environment. "
            f"Payload would have been sent:\n{formatted_message}"
        )
        return formatted_message  # for test verification

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL, json={"content": formatted_message}
        )
        if response.status_code == 204:
            print(f"[+] Alert sent successfully: {severity.upper()} — {message}")
        else:
            print(f"[!] Failed to send alert: HTTP {response.status_code}")
    except Exception as e:
        print(f"[!] Error sending alert: {e}")
