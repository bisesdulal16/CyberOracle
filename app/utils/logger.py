"""
Secure Logging Utilities
========================
Implements masked logging for sensitive fields and safe async log storage.

OWASP Logging Guidance:
- Never log secrets, tokens, passwords, or API keys.
- Always sanitize logs before writing to stdout or the database.
- Ensure logs cannot leak sensitive fields during debugging, auditing, or errors.
"""

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

# Sensitive fields that must NEVER appear in logs (OWASP-ASVS 9.1)
SENSITIVE_PATTERNS = {
    "password": r"password=[^&\s]+",
    "token": r"token=[^&\s]+",
    "api_key": r"api[_-]?key=[^&\s]+",
}


def mask_sensitive(text: str) -> str:
    """
    Mask sensitive values before logging.

    Parameters
    ----------
    text : str
        The message that may contain sensitive info.

    Returns
    -------
    str
        Sanitized message where sensitive fields are masked.

    Notes (OWASP-ASVS 9.1.1)
    ------------------------
    Logging secrets is a critical vulnerability.
    We replace values but keep field names for debugging visibility.
    """
    if not isinstance(text, str):
        return text

    masked = text
    for label, pattern in SENSITIVE_PATTERNS.items():
        masked = re.sub(pattern, f"{label}=***MASKED***", masked, flags=re.IGNORECASE)
    return masked


def secure_log(message: str) -> None:
    """
    Log a message safely using masked output.

    Notes
    -----
    Protects logs from leaking credentials during debugging.
    """
    safe_msg = mask_sensitive(message)
    logger.info(safe_msg)


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

    Params
    ------
    endpoint : str
        Endpoint accessed e.g. "/ai/query"
    method : str
        HTTP method used (GET/POST/etc.)
    status_code : int
        Resulting HTTP status
    message : str, optional
        Additional details, already masked by caller. Encrypted before storage
        if DB_ENCRYPTION_ENABLED=true in the environment.
    event_type : str, optional
        Classifier e.g. "ai_query", "ai_query_blocked", "dlp_alert"
    severity : str, optional
        "low" | "medium" | "high" — derived from risk_score by caller
    risk_score : float, optional
        DLP risk score in [0.0, 1.0]
    source : str, optional
        Originating component e.g. "ai_route", "dlp_middleware"
    policy_decision : str, optional
        DLP outcome: "allow" | "redact" | "block"
    user_id : str, optional
        Authenticated user identifier (reserved for RBAC, future use)

    Security Notes (OWASP-ASVS 9.3)
    --------------------------------
    - Only masked content should be passed as message.
    - Message is additionally Fernet-encrypted when DB_ENCRYPTION_ENABLED=true.
    """
    # Encrypt the message field before DB storage when encryption is active
    stored_message = encrypt_value(message) if message else message
    
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
        )
        session.add(entry)
        await session.commit()
