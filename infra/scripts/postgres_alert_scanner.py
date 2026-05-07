#!/usr/bin/env python3
"""
QTFR9 Postgres Log Alert Scanner
Reads CyberOracle logs from PostgreSQL and prints or emails alerts for errors,
authentication failures, DLP hits, and policy violations.
"""

import argparse
import os
import re
import smtplib
import sys
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable

import psycopg2
from psycopg2.extras import RealDictCursor

HIGH_PATTERNS = {
    "policy_violation": re.compile(r"DLP_HIT|policy_violation|FERPA|HIPAA|GENERIC_SSN|EMAIL_ADDRESS", re.I),
    "authentication": re.compile(r"AUTH_FAILURE|failed login|unauthorized|forbidden|invalid token", re.I),
    "runtime_error": re.compile(r"ERROR|Exception|Traceback|500", re.I),
}

MEDIUM_PATTERNS = {
    "operational_warning": re.compile(r"WARN|rate limit|timeout|slow request", re.I),
}

@dataclass
class Alert:
    log_id: int
    created_at: str
    severity: str
    category: str
    endpoint: str
    status_code: int
    message: str


def classify(message: str, status_code: int) -> tuple[str, str] | None:
    text = message or ""
    for category, pattern in HIGH_PATTERNS.items():
        if pattern.search(text) or status_code >= 500:
            return "HIGH", category
    for category, pattern in MEDIUM_PATTERNS.items():
        if pattern.search(text) or status_code in (401, 403, 429):
            return "MEDIUM", category
    return None


def fetch_recent_logs(dsn: str, minutes: int, min_id: int = 0) -> Iterable[dict]:
    query = """
        SELECT id, endpoint, method, status_code, message, created_at
        FROM logs
        WHERE created_at >= NOW() - (%s || ' minutes')::interval
          AND id > %s
        ORDER BY id ASC;
    """
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (minutes, min_id))
            return cur.fetchall()


def build_alerts(rows: Iterable[dict]) -> list[Alert]:
    alerts = []
    for row in rows:
        result = classify(row.get("message", ""), int(row.get("status_code") or 0))
        if not result:
            continue
        severity, category = result
        alerts.append(Alert(
            log_id=row["id"],
            created_at=str(row["created_at"]),
            severity=severity,
            category=category,
            endpoint=row.get("endpoint", ""),
            status_code=int(row.get("status_code") or 0),
            message=row.get("message", ""),
        ))
    return alerts


def format_alert(alert: Alert) -> str:
    return (
        f"[{alert.severity}] {alert.category} log_id={alert.log_id} "
        f"time={alert.created_at} endpoint={alert.endpoint} status={alert.status_code}\n"
        f"message={alert.message}\n"
    )


def send_email(subject: str, body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_from = os.getenv("ALERT_FROM", smtp_user or "cyberoracle-alerts@example.com")
    mail_to = os.getenv("ALERT_TO")

    if not smtp_host or not mail_to:
        raise RuntimeError("Email mode requires SMTP_HOST and ALERT_TO environment variables.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan CyberOracle Postgres logs and alert on high-severity events.")
    parser.add_argument("--dsn", default=os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:5432/cyberoracle"))
    parser.add_argument("--minutes", type=int, default=15)
    parser.add_argument("--min-id", type=int, default=0)
    parser.add_argument("--email", action="store_true", help="Email alerts using SMTP_* environment variables.")
    args = parser.parse_args()

    rows = fetch_recent_logs(args.dsn, args.minutes, args.min_id)
    alerts = build_alerts(rows)

    if not alerts:
        print("QTFR9 scanner: no alertable events found.")
        return 0

    body = "\n".join(format_alert(alert) for alert in alerts)
    print(body)

    if args.email:
        send_email(f"CyberOracle QTFR9 Alert: {len(alerts)} event(s)", body)
        print("Email alert sent.")

    return 2 if any(alert.severity == "HIGH" for alert in alerts) else 1


if __name__ == "__main__":
    sys.exit(main())
