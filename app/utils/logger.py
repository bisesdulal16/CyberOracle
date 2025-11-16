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
    endpoint: str, method: str, status_code: int, message: str = None
):
    """
    Store structured log entries asynchronously in the database.

    Params
    ------
    endpoint : str
        Endpoint accessed e.g. "/logs/ingest"
    method : str
        HTTP method used (GET/POST/etc.)
    status_code : int
        Resulting HTTP status
    message : str, optional
        Additional details, already masked by caller.

    Security Notes (OWASP-ASVS 9.3)
    --------------------------------
    - Logs must be structured, timestamped, and non-sensitive.
    - Only masked content should ever be inserted into the DB.
    """
    async with AsyncSessionLocal() as session:
        entry = LogEntry(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            message=message,
        )
        session.add(entry)
        await session.commit()
