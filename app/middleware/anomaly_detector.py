"""
Anomaly Detection Middleware
----------------------------
Detects abnormal payloads, suspicious keywords, and excessive request rates.

Triggers alert_manager.send_alert() when anomalies are found.
"""

import json
import time
from fastapi import Request
from app.utils.alert_manager import send_alert

# In-memory rate tracking per IP (simple Week-4-level implementation)
REQUEST_HISTORY = {}  # {ip: [timestamps]}

# Keywords that indicate suspicious or harmful behavior
SUSPICIOUS_KEYWORDS = [
    "DROP TABLE",
    "UNION SELECT",
    "DELETE FROM",
    "api_key",
    "token=",
    "password=",
    "sk_live_",
]


async def anomaly_detector(request: Request, call_next):
    
    client_ip = request.client.host
    now = time.time()

    # ---------------------------------------------------------
    # 1) Rate-limit anomaly: > 5 requests in 10 seconds
    # ---------------------------------------------------------
    timestamps = REQUEST_HISTORY.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < 10]
    timestamps.append(now)
    REQUEST_HISTORY[client_ip] = timestamps

    if len(timestamps) > 5:
        send_alert(
            f"Rate Anomaly: High request volume from {client_ip}",
            severity="medium",
            source="anomaly_detector",
        )

    # ---------------------------------------------------------
    # 2) Large payload anomaly (> 5 KB)
    # ---------------------------------------------------------
    try:
        raw_body = await request.body()
        if len(raw_body) > 5 * 1024:  # 5 KB
            send_alert(
                f"Payload Anomaly: Request body too large ({len(raw_body)} bytes)",
                severity="medium",
                source="anomaly_detector",
            )
    except Exception:
        pass

    # ---------------------------------------------------------
    # 3) Suspicious keyword anomaly
    # ---------------------------------------------------------
    try:
        body_text = raw_body.decode("utf-8")
        if any(keyword.lower() in body_text.lower() for keyword in SUSPICIOUS_KEYWORDS):
            send_alert(
                "Suspicious Keyword Detected in payload",
                severity="high",
                source="anomaly_detector",
            )
    except Exception:
        pass

    # Allow request to continue
    response = await call_next(request)
    return response
