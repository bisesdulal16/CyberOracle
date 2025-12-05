"""
Secure Logging Utilities (NCFR5)
===============================
Implements masked logging for sensitive fields and safe async log storage.

OWASP Logging Guidance:
- Never log secrets, tokens, passwords, SSNs, or API keys.
- Always sanitize logs before writing to stdout or the database.
"""

import logging
import re
from app.db.db import AsyncSessionLocal
from app.models import LogEntry

# -------------------------------------------------------------------------
# Configure secure application logger
# -------------------------------------------------------------------------

logger = logging.getLogger("cyberoracle")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Sensitive fields that must NEVER appear in logs (OWASP-ASVS 9.1)
SENSITIVE_PATTERNS = {
    # query-string style
    "password": r"(password=)[^&\s]+",
    "token": r"(token=)[^&\s]+",
    "api_key": r"(api[_-]?key=)[^&\s]+",
    # JSON style: "password": "value"
    "password_json": r"(\"password\"\s*:\s*\")[^\"]+",
    "token_json": r"(\"token\"\s*:\s*\")[^\"]+",
    "ssn_json": r"(\"ssn\"\s*:\s*\")[^\"]+",
}


def mask_sensitive(text: str) -> str:
    """
    Mask sensitive values before logging.
    This ensures logs never reveal secrets.
    """
    if not isinstance(text, str):
        return text

    masked = text

    for label, pattern in SENSITIVE_PATTERNS.items():
        field = label.split("_")[0]  # normalize "password_json" → "password"
        masked = re.sub(
            pattern, f'"{field}": "***MASKED***"', masked, flags=re.IGNORECASE
        )

    return masked


def secure_log(message: str) -> None:
    """
    Public logging helper that masks sensitive data prior to stdout logging.
    """
    safe_msg = mask_sensitive(message)
    logger.info(safe_msg)


async def log_request(
    endpoint: str, method: str, status_code: int, message: str = None
):
    """
    Store structured log entries asynchronously in the database.
    Sensitive data is masked before insertion.
    """
    safe_message = mask_sensitive(message) if message else None

    async with AsyncSessionLocal() as session:
        entry = LogEntry(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            message=safe_message,
        )
        session.add(entry)
        await session.commit()

    # Also log masked version to stdout
    logger.info(f"[REQUEST] {endpoint} {method} {status_code} → {safe_message}")
