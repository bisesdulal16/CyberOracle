#!/usr/bin/env python3
"""
scripts/anomaly_alerting.py

PSFR6 — Alerting logic for suspicious activity anomalies.

Detects:
  1. Rate-based anomalies  — IPs exceeding request threshold in a time window
  2. Payload size anomalies — requests with unusually large prompt sizes
  3. High-risk score events — DLP risk scores above threshold
  4. Repeated DLP blocks    — same IP blocked multiple times

Sends alerts to Discord via alert_manager.py when anomalies are detected.
"""

import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.utils.alert_manager import send_alert

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
BASE_URL = os.getenv("CYBERORACLE_BASE_URL", "http://localhost:8001")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "changeme_admin")

RATE_THRESHOLD = 5        # flag if same IP appears more than this in logs
PAYLOAD_SIZE_THRESHOLD = 500  # characters — flag unusually large prompts
RISK_SCORE_THRESHOLD = 0.7    # flag high-risk DLP events
BLOCK_REPEAT_THRESHOLD = 2    # flag IPs blocked more than this many times


def get_token() -> str:
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def log_anomaly_to_ui(token: str, anomaly_type: str, message: str, severity: str = "high"):
    """Write anomaly directly to DB so it appears in the UI Alerts tab."""
    try:
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.db.db import AsyncSessionLocal
        from app.models import LogEntry
        from datetime import datetime, timezone

        async def _insert():
            async with AsyncSessionLocal() as session:
                entry = LogEntry()
                entry.endpoint = "/anomaly-detection"
                entry.method = "SYSTEM"
                entry.status_code = 200
                entry.message = f"[ANOMALY:{anomaly_type}] {message}"
                entry.event_type = "anomaly_detected"
                entry.severity = severity
                entry.risk_score = 1.0 if severity == "high" else 0.7
                entry.source = "anomaly_alerting"
                entry.policy_decision = "block"
                entry.created_at = datetime.now(timezone.utc)
                session.add(entry)
                await session.commit()

        asyncio.run(_insert())
        print(f"    [UI] Anomaly logged to dashboard.")
    except Exception as e:
        print(f"    [UI] Failed to log to dashboard: {e}")


def fetch_logs(token: str) -> list:
    resp = requests.get(
        f"{BASE_URL}/logs/list?limit=100",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("logs", [])


def check_rate_anomaly(logs: list) -> list:
    """Detect IPs with unusually high request counts."""
    from collections import Counter
    ip_counts = Counter()
    for log in logs:
        msg = log.get("message", "")
        if "client_ip" in msg:
            try:
                ip = msg.split("'client_ip': '")[1].split("'")[0]
                ip_counts[ip] += 1
            except IndexError:
                pass
    return [
        {"ip": ip, "count": count}
        for ip, count in ip_counts.items()
        if count > RATE_THRESHOLD
    ]


def check_payload_anomaly(logs: list) -> list:
    """Detect logs with unusually large input payloads."""
    flagged = []
    for log in logs:
        msg = log.get("message", "")
        if "input_preview" in msg:
            try:
                preview = msg.split("'input_preview': '")[1].split("'")[0]
                if len(preview) > PAYLOAD_SIZE_THRESHOLD:
                    flagged.append({
                        "id": log.get("id"),
                        "size": len(preview),
                        "preview": preview[:100] + "..."
                    })
            except IndexError:
                pass
    return flagged


def check_high_risk(logs: list) -> list:
    """Detect events with high DLP risk scores."""
    return [
        {
            "id": log.get("id"),
            "risk_score": log.get("risk_score"),
            "endpoint": log.get("endpoint"),
            "decision": log.get("policy_decision"),
        }
        for log in logs
        if (log.get("risk_score") or 0) >= RISK_SCORE_THRESHOLD
    ]


def check_repeated_blocks(logs: list) -> list:
    """Detect IPs that have been blocked multiple times."""
    from collections import Counter
    block_counts = Counter()
    for log in logs:
        if log.get("policy_decision") == "block":
            msg = log.get("message", "")
            if "client_ip" in msg:
                try:
                    ip = msg.split("'client_ip': '")[1].split("'")[0]
                    block_counts[ip] += 1
                except IndexError:
                    pass
    return [
        {"ip": ip, "blocks": count}
        for ip, count in block_counts.items()
        if count >= BLOCK_REPEAT_THRESHOLD
    ]


def run():
    print("=" * 60)
    print("  CyberOracle Anomaly Detection & Alerting")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    print("\n[1] Authenticating...")
    token = get_token()
    print("    Token obtained.")

    print("\n[2] Fetching recent logs...")
    logs = fetch_logs(token)
    print(f"    {len(logs)} log entries loaded.")

    anomalies_found = 0

    # --- Rate anomaly ---
    print("\n[3] Checking rate-based anomalies...")
    rate_hits = check_rate_anomaly(logs)
    if rate_hits:
        for hit in rate_hits:
            print(f"    ANOMALY: IP {hit['ip']} made {hit['count']} requests (threshold: {RATE_THRESHOLD})")
            msg = f"Rate Anomaly: IP {hit['ip']} made {hit['count']} requests (threshold: {RATE_THRESHOLD}). Action: Investigate or block."
            send_alert(msg, severity="warning", source="anomaly_alerting")
            log_anomaly_to_ui(token, "RATE_ANOMALY", msg, severity="high")
            anomalies_found += 1
    else:
        print("    No rate anomalies detected.")

    # --- Payload size anomaly ---
    print("\n[4] Checking payload size anomalies...")
    payload_hits = check_payload_anomaly(logs)
    if payload_hits:
        for hit in payload_hits:
            print(f"    ANOMALY: Log #{hit['id']} has large payload ({hit['size']} chars)")
            msg = f"Large Payload: Log #{hit['id']} — {hit['size']} chars (threshold: {PAYLOAD_SIZE_THRESHOLD}). Preview: {hit['preview']}"
            send_alert(msg, severity="warning", source="anomaly_alerting")
            log_anomaly_to_ui(token, "PAYLOAD_ANOMALY", msg, severity="high")
            anomalies_found += 1
    else:
        print("    No payload size anomalies detected.")

    # --- High risk score ---
    print("\n[5] Checking high-risk DLP events...")
    risk_hits = check_high_risk(logs)
    if risk_hits:
        for hit in risk_hits[:3]:
            print(f"    ANOMALY: Log #{hit['id']} risk={hit['risk_score']} decision={hit['decision']}")
            msg = f"High-Risk DLP: Log #{hit['id']} on {hit['endpoint']} — risk={hit['risk_score']} decision={hit['decision']}. Immediate review required."
            send_alert(msg, severity="critical", source="anomaly_alerting")
            log_anomaly_to_ui(token, "HIGH_RISK_DLP", msg, severity="high")
            anomalies_found += 1
        if len(risk_hits) > 3:
            print(f"    ... and {len(risk_hits)-3} more high-risk events.")
    else:
        print("    No high-risk events detected.")

    # --- Repeated blocks ---
    print("\n[6] Checking repeated DLP blocks...")
    block_hits = check_repeated_blocks(logs)
    if block_hits:
        for hit in block_hits:
            print(f"    ANOMALY: IP {hit['ip']} blocked {hit['blocks']} times")
            msg = f"Repeated Blocks: IP {hit['ip']} blocked {hit['blocks']} times (threshold: {BLOCK_REPEAT_THRESHOLD}). Consider permanent ban."
            send_alert(msg, severity="high", source="anomaly_alerting")
            log_anomaly_to_ui(token, "REPEATED_BLOCK", msg, severity="high")
            anomalies_found += 1
    else:
        print("    No repeated block anomalies detected.")

    print("\n" + "=" * 60)
    print(f"  Scan Complete — {anomalies_found} anomalies detected and alerted.")
    print("=" * 60)


if __name__ == "__main__":
    run()
