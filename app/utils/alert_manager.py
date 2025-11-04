"""
Alert Manager — Discord Integration
-----------------------------------
CyberOracle Week 4: Real-Time Alerting System
Sends alert messages to a Discord channel via webhook.

Usage:
    from app.utils.alert_manager import send_alert
    send_alert("Sensitive data detected", severity="critical", source="DLP Middleware")
"""

import os
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_alert(message: str, severity: str = "info", source: str = "system"):
    """
    Sends a formatted alert message to Discord via webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        print("[!] Discord webhook not set in environment.")
        return

    # Emoji mapping based on severity
    emojis = {"critical": "🚨", "high": "⚠️", "medium": "🔶", "low": "ℹ️"}

    emoji = emojis.get(severity.lower(), "📢")

    payload = {
        "content": (
            f"{emoji} **{severity.upper()}** alert from `{source}`\n"
            f"> {message}\n\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code != 204:
            print(
                f"[!] Discord webhook failed: {response.status_code}, {response.text}"
            )
        else:
            print(f"[+] Alert sent successfully: {severity.upper()} — {message}")
    except Exception as e:
        print(f"[!] Error sending Discord alert: {e}")
