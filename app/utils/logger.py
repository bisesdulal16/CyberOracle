"""
Secure Logging Utilities
========================
Implements masked logging for sensitive fields and safe async log storage.

OWASP Logging Guidance (OWASP-ASVS 9.1):
- Never log secrets, tokens, passwords, SSNs, or credit card numbers.
- Always sanitize logs before writing to stdout or the database.
- Apply masking as a final safety net even if callers pre-mask.
- Encrypt stored log messages when DB_ENCRYPTION_ENABLED=true.
- Compute integrity hash for tamper-evidence (OWASP-ASVS 9.5).
"""

import hashlib
import logging
import re
from typing import Optional

from app.db.db import AsyncSessionLocal
from app.models import LogEntry
from app.utils.db_encryption import encrypt_value

# -------------------------------------------------------------------------
# Configure secure application logger
# -------------------------------------------------------------------------

logger = logging.getLogger("cyberoracle")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# -------------------------------------------------------------------------
# Sensitive patterns — OWASP-ASVS 9.1.1
# Covers query-string, JSON, header, and raw value formats
# -------------------------------------------------------------------------
SENSITIVE_PATTERNS = {
    # Passwords in any format: password=abc, "password": "abc", password: abc
    "password": r"(?i)password['\"]?\s*[:=]\s*['\"]?[^\s,'\"\}&]+",

    # Bearer tokens and JWT values
    "token": r"(?i)(bearer\s+|token['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9\-_\.]+",

    # API keys in any format
    "api_key": r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"]?[^\s,'\"\}&]+",

    # US Social Security Numbers
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",

    # Credit card numbers (major card types)
    "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",

    # Email addresses
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",

    # Authorization headers
    "authorization": r"(?i)authorization['\"]?\s*[:=]\s*['\"]?[^\s,'\"\}&]+",
}


def mask_sensitive(text: str) -> str:
    """
    Mask sensitive values before logging or storing.

    Covers passwords, tokens, API keys, SSNs, credit cards,
    emails, and authorization headers in any common format.

    Parameters
    ----------
    text : str
        The message that may contain sensitive info.

    Returns
    -------
    str
        Sanitized message where sensitive values are replaced
        with ***MASKED*** while keeping field names visible
        for debugging.

    Notes (OWASP-ASVS 9.1.1)
    ------------------------
    Logging secrets is a critical vulnerability that can lead
    to credential theft, compliance violations, and data breaches.
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""

    masked = text
    for label, pattern in SENSITIVE_PATTERNS.items():
        masked = re.sub(
            pattern,
            f"***{label.upper()}_MASKED***",
            masked,
            flags=re.IGNORECASE,
        )
    return masked


def secure_log(message: str) -> None:
    """
    Log a message safely after applying sensitive data masking.

    Always use this instead of logger.info() directly to ensure
    no sensitive data reaches log output.
    """
    safe_msg = mask_sensitive(message)
    logger.info(safe_msg)


def compute_log_hash(
    endpoint: str,
    method: str,
    status_code: int,
    message: Optional[str],
    event_type: Optional[str],
) -> str:
    """
    Compute a SHA-256 integrity hash over core log fields.

    Used for tamper-evidence detection (OWASP-ASVS 9.5).
    If any field is modified after storage, the hash will
    no longer match and the entry is flagged as tampered.

    Parameters
    ----------
    endpoint    : API endpoint string
    method      : HTTP method
    status_code : HTTP response status
    message     : Log message (pre-masked)
    event_type  : Event classification string

    Returns
    -------
    str
        64-character hex SHA-256 digest
    """
    raw = "|".join([
        str(endpoint or ""),
        str(method or ""),
        str(status_code or ""),
        str(message or ""),
        str(event_type or ""),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    message: str = None,
    event_type: Optional[str] = None,
    frameworks: list = None,
    decision: str = None,
    severity: Optional[str] = None,
    risk_score: Optional[float] = None,
    source: Optional[str] = None,
    policy_decision: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Store structured log entries asynchronously in the database.

    Applies mask_sensitive() as a final safety net before storage,
    computes an integrity hash for tamper-evidence detection,
    and encrypts the message field with Fernet when
    DB_ENCRYPTION_ENABLED=true.

    Security Notes (OWASP-ASVS 9.3, 9.5)
    --------------------------------------
    - mask_sensitive() applied as defence-in-depth.
    - Integrity hash computed before encryption for verification.
    - Message encrypted at rest.
    """
    # Apply masking as a final safety net
    safe_message = mask_sensitive(message) if message else message

    # Compute integrity hash BEFORE encryption so we can verify on read
    integrity_hash = compute_log_hash(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        message=safe_message,
        event_type=event_type,
    )

    # Encrypt the masked message before DB storage
    stored_message = encrypt_value(safe_message) if safe_message else safe_message

    frameworks_str = ", ".join(frameworks) if frameworks else None

    async with AsyncSessionLocal() as session:
        entry = LogEntry(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            message=stored_message,
            event_type=event_type,
            frameworks=frameworks_str,
            decision=decision,
            severity=severity,
            risk_score=risk_score,
            source=source,
            policy_decision=policy_decision,
            integrity_hash=integrity_hash,
        )
        session.add(entry)
        await session.commit()